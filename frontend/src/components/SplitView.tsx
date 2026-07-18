import type { ReactNode } from 'react'

interface SplitViewProps {
  left: ReactNode
  right: ReactNode
  leftLabel?: string
  rightLabel?: string
}

export default function SplitView({ left, right }: SplitViewProps) {
  return (
    <div
      id="split-view"
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 2px 1fr',
        gap: 0,
        minHeight: 600,
        background: 'var(--surface-card)',
        border: '1px solid var(--border-brass)',
        borderRadius: 4,
        overflow: 'hidden',
      }}
    >
      {/* Prosecution side */}
      <div
        id="split-prosecution"
        style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}
      >
        {left}
      </div>

      {/* Divider */}
      <div
        style={{
          background: 'linear-gradient(to bottom, var(--saffron), var(--brass))',
          opacity: 0.3,
          flexShrink: 0,
        }}
      />

      {/* Defense side */}
      <div
        id="split-defense"
        style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}
      >
        {right}
      </div>
    </div>
  )
}
