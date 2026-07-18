import { useEffect, useState } from 'react'
import ScaleScene from '../three/ScaleScene'

interface ScaleHeroProps {
  /**
   * 0 = balanced, negative = prosecution tips down, positive = defense tips down
   */
  tiltDirection?: number
}

export default function ScaleHero({ tiltDirection = 0 }: ScaleHeroProps) {
  const [prefersReduced, setPrefersReduced] = useState(false)
  const [scrollY, setScrollY] = useState(0)

  // Detect prefers-reduced-motion
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReduced(mq.matches)
    const handler = (e: MediaQueryListEvent) => setPrefersReduced(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  // Scroll-reactive tilt
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.scrollY
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight
      const normalized = maxScroll > 0 ? scrollTop / maxScroll : 0
      setScrollY(normalized)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Static fallback for reduced-motion
  if (prefersReduced) {
    return (
      <div
        className="hero-canvas"
        role="img"
        aria-label="A static illustration of the Nyaya Tarazu scales of justice"
        style={{ alignItems: 'center', justifyContent: 'center' }}
      >
        <img
          src="/logo.png"
          alt="Nyaya Tarazu scales of justice"
          style={{ maxHeight: 320, opacity: 0.9 }}
        />
      </div>
    )
  }

  return (
    <div
      className="hero-canvas"
      aria-hidden="true"
      id="scale-hero-3d"
    >
      <ScaleScene scrollY={scrollY + tiltDirection} />
    </div>
  )
}
