import CitationChip from './CitationChip'

interface BriefSectionData {
  heading: string
  content: string
  citations: string[]
}

interface CitationVerification {
  citation: string
  verified: boolean
  flag_reason?: string
}

interface BriefData {
  persona: 'prosecution' | 'defense'
  issues: string[]
  applicable_provisions: BriefSectionData[]
  arguments: BriefSectionData[]
  supporting_precedents: BriefSectionData[]
  prayer: string
  citation_verifications?: CitationVerification[]
  disclaimer?: string
}

interface BriefPanelProps {
  brief: BriefData
  onExport?: (persona: string) => void
  isExporting?: boolean
}

function buildVerificationMap(verifications?: CitationVerification[]): Record<string, CitationVerification> {
  const map: Record<string, CitationVerification> = {}
  for (const v of (verifications || [])) {
    map[v.citation] = v
  }
  return map
}

function SectionBlock({
  section,
  verificationMap,
}: {
  section: BriefSectionData
  verificationMap: Record<string, CitationVerification>
}) {
  return (
    <div className="brief-section">
      <div className="brief-section-heading">{section.heading}</div>
      <p style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', lineHeight: 1.8, marginBottom: 8 }}>
        {section.content}
      </p>
      {section.citations.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
          {section.citations.map((cit) => {
            const v = verificationMap[cit]
            return (
              <CitationChip
                key={cit}
                citation={cit}
                verified={v ? v.verified : true}
                previewText={v && !v.verified ? v.flag_reason : undefined}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function BriefPanel({ brief, onExport, isExporting }: BriefPanelProps) {
  const isProsecution = brief.persona === 'prosecution'
  const verificationMap = buildVerificationMap(brief.citation_verifications)
  const unverifiedCount = (brief.citation_verifications || []).filter(v => !v.verified).length

  return (
    <div className="brief-panel" id={`brief-panel-${brief.persona}`}>
      {/* Header */}
      <div className={`brief-panel-header ${brief.persona}`}>
        <div>
          <div className={`brief-panel-persona ${brief.persona}`}>
            {isProsecution ? '⚖ Prosecution' : '🛡 Defense'}
          </div>
          {unverifiedCount > 0 && (
            <div style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--oxblood)',
              marginTop: 2,
              fontFamily: 'var(--font-mono)',
            }}>
              ⚠ {unverifiedCount} citation{unverifiedCount > 1 ? 's' : ''} require{unverifiedCount === 1 ? 's' : ''} verification
            </div>
          )}
        </div>
        {onExport && (
          <button
            className="btn btn-secondary"
            id={`export-btn-${brief.persona}`}
            onClick={() => onExport(brief.persona)}
            disabled={isExporting}
            style={{ fontSize: 'var(--text-xs)', padding: '0.4rem 0.875rem' }}
          >
            {isExporting ? 'Exporting…' : 'Export .docx'}
          </button>
        )}
      </div>

      {/* Disclaimer */}
      <div style={{ padding: '0.5rem var(--space-6)', borderBottom: '1px solid var(--border-brass)' }}>
        <div className="disclaimer">
          {brief.disclaimer || 'AI-generated draft. Verify against original sources before relying on this in any proceeding.'}
        </div>
      </div>

      {/* Body */}
      <div className="brief-panel-body">

        {/* Issues */}
        {brief.issues.length > 0 && (
          <div className="brief-section" style={{ marginBottom: 'var(--space-6)' }}>
            <div className="brief-section-heading">Issues</div>
            <ol style={{ paddingLeft: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {brief.issues.map((issue, i) => (
                <li key={i} style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-sm)', lineHeight: 1.7 }}>
                  {issue}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Applicable Provisions */}
        {brief.applicable_provisions.length > 0 && (
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <div className="brief-section-heading" style={{ marginBottom: 'var(--space-3)' }}>Applicable Provisions</div>
            {brief.applicable_provisions.map((s, i) => (
              <SectionBlock key={i} section={s} verificationMap={verificationMap} />
            ))}
          </div>
        )}

        {/* Arguments */}
        {brief.arguments.length > 0 && (
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <div className="brief-section-heading" style={{ marginBottom: 'var(--space-3)' }}>Arguments</div>
            {brief.arguments.map((s, i) => (
              <SectionBlock key={i} section={s} verificationMap={verificationMap} />
            ))}
          </div>
        )}

        {/* Precedents */}
        {brief.supporting_precedents.length > 0 && (
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <div className="brief-section-heading" style={{ marginBottom: 'var(--space-3)' }}>Supporting Precedents</div>
            {brief.supporting_precedents.map((s, i) => (
              <SectionBlock key={i} section={s} verificationMap={verificationMap} />
            ))}
          </div>
        )}

        {/* Prayer */}
        {brief.prayer && (
          <div className="brief-section">
            <div className="brief-section-heading">Prayer / Relief Sought</div>
            <p style={{
              fontFamily: 'var(--font-display)',
              fontSize: 'var(--text-sm)',
              lineHeight: 1.8,
              borderLeft: `3px solid ${isProsecution ? 'var(--saffron)' : 'var(--brass)'}`,
              paddingLeft: 'var(--space-4)',
              marginTop: 'var(--space-2)',
            }}>
              {brief.prayer}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
