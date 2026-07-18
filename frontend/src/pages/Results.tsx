import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { BriefResponse, ExtractedFacts } from '../services/api'
import { exportBrief } from '../services/api'
import SplitView from '../components/SplitView'
import BriefPanel from '../components/BriefPanel'

interface ResultsProps {
  brief: BriefResponse | null
  facts: ExtractedFacts | null
}

export default function Results({ brief, facts }: ResultsProps) {
  const navigate = useNavigate()
  const [exportingPersona, setExportingPersona] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  if (!brief || !facts) {
    return (
      <main className="page" id="results-page">
        <div className="container" style={{ padding: 'var(--space-16)', textAlign: 'center' }}>
          <p style={{ opacity: 0.5 }}>No case loaded yet — paste the facts to begin.</p>
          <button className="btn btn-primary" onClick={() => navigate('/intake')} style={{ marginTop: 'var(--space-6)' }}>
            Start a case
          </button>
        </div>
      </main>
    )
  }

  const handleExport = async (persona: string) => {
    const briefData = persona === 'prosecution' ? brief.prosecution : brief.defense
    setExportingPersona(persona)
    setExportError(null)
    try {
      const blob = await exportBrief(
        briefData,
        'docx',
        facts.offence_type ? `${facts.offence_type} case` : undefined,
      )
      // Trigger download
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `nyaya_tarazu_${persona}_brief.docx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err: any) {
      setExportError(`Couldn't export ${persona} brief: ${err.message}`)
    } finally {
      setExportingPersona(null)
    }
  }

  const unverifiedTotal = [
    ...brief.prosecution.citation_verifications,
    ...brief.defense.citation_verifications,
  ].filter(c => !c.verified).length

  return (
    <main className="page" id="results-page">
      <div style={{ padding: 'var(--space-6) 0', borderBottom: '1px solid var(--border-brass)' }}>
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
            <div>
              <p className="hero-kicker" style={{ marginBottom: 'var(--space-1)' }}>Results</p>
              <h1 style={{ fontSize: 'var(--text-lg)', margin: 0 }}>
                {facts.offence_type || 'Case'} — {facts.code_era === 'old' ? 'IPC/CrPC' : 'BNS/BNSS/BSA'}
              </h1>
            </div>
            <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
              <button
                className="btn btn-ghost"
                id="results-edit-btn"
                onClick={() => navigate('/confirm')}
                style={{ fontSize: 'var(--text-xs)' }}
              >
                ← Edit facts
              </button>
              <button
                className="btn btn-ghost"
                id="results-new-btn"
                onClick={() => navigate('/intake')}
                style={{ fontSize: 'var(--text-xs)' }}
              >
                New case
              </button>
              <button
                className="btn btn-secondary"
                id="results-lookup-btn"
                onClick={() => navigate('/lookup')}
                style={{ fontSize: 'var(--text-xs)' }}
              >
                Section lookup →
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container" style={{ padding: 'var(--space-6) var(--space-8)' }}>
        {/* Persistent disclaimer */}
        <div className="disclaimer" style={{ marginBottom: 'var(--space-4)' }}>
          AI-generated draft. Verify against original sources before relying on this in any proceeding.
          {unverifiedTotal > 0 && (
            <span style={{ marginLeft: 8, color: 'var(--oxblood)', fontWeight: 600 }}>
              · {unverifiedTotal} citation{unverifiedTotal > 1 ? 's' : ''} require{unverifiedTotal === 1 ? 's' : ''} manual verification.
            </span>
          )}
        </div>

        {/* Export error */}
        {exportError && (
          <div role="alert" style={{
            background: 'rgba(122,46,46,0.15)',
            border: '1px solid rgba(122,46,46,0.4)',
            borderRadius: 3, padding: 'var(--space-3)',
            fontSize: 'var(--text-sm)', color: '#E07070',
            marginBottom: 'var(--space-4)',
          }}>
            {exportError}
          </div>
        )}

        {/* Split brief view */}
        <SplitView
          left={
            <BriefPanel
              brief={brief.prosecution}
              onExport={handleExport}
              isExporting={exportingPersona === 'prosecution'}
            />
          }
          right={
            <BriefPanel
              brief={brief.defense}
              onExport={handleExport}
              isExporting={exportingPersona === 'defense'}
            />
          }
        />

        {/* Retrieved sections (collapsed) */}
        <details style={{ marginTop: 'var(--space-8)' }} id="retrieved-sections">
          <summary
            style={{
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: 'var(--text-xs)',
              color: 'var(--brass)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              opacity: 0.6,
              userSelect: 'none',
              marginBottom: 'var(--space-4)',
            }}
          >
            Retrieved sections ({brief.retrieval_context.length} sections used as context)
          </summary>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {brief.retrieval_context.map((s, i) => (
              <div key={i} className="card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-2)', alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--brass)' }}>
                    {s.act_name} §{s.section_number || '?'}
                  </span>
                  <span style={{ fontSize: 'var(--text-xs)', opacity: 0.4 }}>
                    {s.code_era === 'old' ? 'old code' : 'new code'} · p.{s.page_number}
                  </span>
                </div>
                <p style={{ fontSize: 'var(--text-xs)', opacity: 0.7, lineHeight: 1.6, fontFamily: 'var(--font-body)' }}>
                  {s.chunk_text.slice(0, 300)}{s.chunk_text.length > 300 ? '…' : ''}
                </p>
              </div>
            ))}
          </div>
        </details>
      </div>
    </main>
  )
}
