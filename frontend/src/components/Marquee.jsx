export default function Marquee({ items, speed = 32 }) {
  const track = [...items, ...items]

  return (
    <div className="marquee" style={{ '--marquee-speed': `${speed}s` }}>
      <div className="marquee__track">
        {track.map((item, i) => (
          <span key={`${item}-${i}`} className="marquee__item">
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}
