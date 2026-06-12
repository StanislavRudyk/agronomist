import { useEffect, useRef, useState } from 'react'

export function useScrollReveal(deps = []) {
  useEffect(() => {
    const nodes = document.querySelectorAll('[data-reveal]')
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.08, rootMargin: '0px 0px -60px 0px' }
    )
    nodes.forEach((node) => observer.observe(node))
    return () => observer.disconnect()
  }, deps)
}

export function useScrollProgress() {
  useEffect(() => {
    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight
      const progress = max > 0 ? window.scrollY / max : 0
      document.documentElement.style.setProperty('--scroll-p', progress.toFixed(4))
    }
    update()
    window.addEventListener('scroll', update, { passive: true })
    window.addEventListener('resize', update)
    return () => {
      window.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
    }
  }, [])
}

export function useParallax() {
  useEffect(() => {
    let frame = null
    const update = () => {
      frame = null
      document.querySelectorAll('[data-parallax]').forEach((el) => {
        const speed = parseFloat(el.dataset.parallax || '0.12')
        const rect = el.getBoundingClientRect()
        const offset = (rect.top + rect.height * 0.5 - window.innerHeight * 0.5) * speed
        el.style.setProperty('--parallax-y', `${offset}px`)
      })
    }
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update)
    }
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
      if (frame) cancelAnimationFrame(frame)
    }
  }, [])
}

export function useMouseGlow() {
  useEffect(() => {
    if (window.matchMedia('(pointer: coarse)').matches) return undefined

    const glow = document.createElement('div')
    glow.className = 'mouse-glow'
    document.body.appendChild(glow)

    let x = 0
    let y = 0
    let tx = 0
    let ty = 0
    let frame = null

    const onMove = (e) => {
      tx = e.clientX
      ty = e.clientY
      if (!frame) {
        frame = requestAnimationFrame(tick)
      }
    }

    const tick = () => {
      x += (tx - x) * 0.12
      y += (ty - y) * 0.12
      glow.style.transform = `translate(${x - 180}px, ${y - 180}px)`
      frame = Math.abs(tx - x) > 0.5 || Math.abs(ty - y) > 0.5
        ? requestAnimationFrame(tick)
        : null
    }

    window.addEventListener('mousemove', onMove, { passive: true })
    return () => {
      window.removeEventListener('mousemove', onMove)
      if (frame) cancelAnimationFrame(frame)
      glow.remove()
    }
  }, [])
}

export function useCountUp(target, active, duration = 1800) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    if (!active) return undefined

    let start = null
    let frame = null
    const from = 0
    const to = typeof target === 'number' ? target : parseFloat(target)

    const step = (ts) => {
      if (!start) start = ts
      const t = Math.min((ts - start) / duration, 1)
      const eased = 1 - (1 - t) ** 3
      setValue(from + (to - from) * eased)
      if (t < 1) frame = requestAnimationFrame(step)
    }

    frame = requestAnimationFrame(step)
    return () => {
      if (frame) cancelAnimationFrame(frame)
    }
  }, [target, active, duration])

  return value
}

export function useInView(ref, margin = '-80px') {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const node = ref.current
    if (!node) return undefined

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { rootMargin: `0px 0px ${margin} 0px`, threshold: 0.2 }
    )

    observer.observe(node)
    return () => observer.disconnect()
  }, [margin])

  return visible
}

export function useTilt(intensity = 10) {
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el || window.matchMedia('(pointer: coarse)').matches) return undefined

    const onMove = (e) => {
      const rect = el.getBoundingClientRect()
      const x = (e.clientX - rect.left) / rect.width - 0.5
      const y = (e.clientY - rect.top) / rect.height - 0.5
      el.style.setProperty('--tilt-x', `${-y * intensity}deg`)
      el.style.setProperty('--tilt-y', `${x * intensity}deg`)
      el.style.setProperty('--tilt-lift', '-6px')
      el.style.setProperty('--mouse-x', `${((e.clientX - rect.left) / rect.width) * 100}%`)
      el.style.setProperty('--mouse-y', `${((e.clientY - rect.top) / rect.height) * 100}%`)
    }

    const onLeave = () => {
      el.style.setProperty('--tilt-x', '0deg')
      el.style.setProperty('--tilt-y', '0deg')
      el.style.setProperty('--tilt-lift', '0px')
      el.style.setProperty('--mouse-x', '50%')
      el.style.setProperty('--mouse-y', '50%')
    }

    el.addEventListener('mousemove', onMove)
    el.addEventListener('mouseleave', onLeave)
    return () => {
      el.removeEventListener('mousemove', onMove)
      el.removeEventListener('mouseleave', onLeave)
    }
  }, [intensity])

  return ref
}
