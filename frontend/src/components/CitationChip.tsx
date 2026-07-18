import { useState } from 'react'

interface CitationChipProps {
  citation: string
  verified?: boolean
  previewText?: string
}

export default function CitationChip({ citation, verified = true, previewText }: CitationChipProps) {
  const [showPreview, setShowPreview] = useState(false)

  return (
    <span style={{ position: 'relative', display: 'inline-block' }}>
      <span
        className={`citation ${!verified ? 'unverified' : ''}`}
        id={`citation-${citation.replace(/\s/g, '-')}`}
        title={verified ? 'Citation verified in corpus' : 'Not found in corpus — verify manually'}
        onMouseEnter={() => previewText && setShowPreview(true)}
        onMouseLeave={() => setShowPreview(false)}
        onFocus={() => previewText && setShowPreview(true)}
        onBlur={() => setShowPreview(false)}
        tabIndex={0}
        role="button"
        aria-label={`${citation} — ${verified ? 'verified' : 'unverified, verify manually'}`}
      >
        {!verified && <span aria-hidden="true" style={{ marginRight: 4 }}>⚠</span>}
        {citation}
      </span>

      {/* Hover preview tooltip */}
      {showPreview && previewText && (
        <div
          role="tooltip"
          style={{
            position: 'absolute',
            bottom: '100%',
            left: 0,
            marginBottom: 6,
            width: 340,
            background: 'var(--surface-card)',
            border: '1px solid var(--border-brass-mid)',
            borderRadius: 3,
            padding: '0.75rem 1rem',
            fontSize: 'var(--text-xs)',
            fontFamily: 'var(--font-body)',
            color: 'var(--parchment)',
            lineHeight: 1.6,
            zIndex: 50,
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          }}
        >
          <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--brass)', marginBottom: 6, fontSize: '0.7rem', letterSpacing: '0.1em' }}>
            {citation}
          </div>
          {previewText}
        </div>
      )}
    </span>
  )
}
