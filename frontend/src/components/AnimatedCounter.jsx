import { useRef } from 'react'
import { useCountUp, useInView } from '../hooks/useMotion'

export default function AnimatedCounter({
  value,
  suffix = '',
  prefix = '',
  decimals = 0,
  className = '',
}) {
  const ref = useRef(null)
  const visible = useInView(ref)
  const current = useCountUp(value, visible)

  const formatted = decimals > 0
    ? current.toFixed(decimals)
    : Math.round(current).toString()

  return (
    <strong ref={ref} className={className}>
      {prefix}{formatted}{suffix}
    </strong>
  )
}
