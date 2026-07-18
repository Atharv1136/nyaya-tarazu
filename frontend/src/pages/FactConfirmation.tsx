import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { ExtractedFacts } from '../services/api'
import { retrieveSections, generateBriefs, type BriefResponse } from '../services/api'
import ProgressStepper, { type Step } from '../components/ProgressStepper'

interface FactConfirmationProps {
  facts: ExtractedFacts | null
  onBriefGenerated: (brief: BriefResponse, facts: ExtractedFacts) => void
}

const INITIAL_STEPS: Step[] = [
  { id: 'retrieve', label: 'Retrieving relevant sections', status: 'pending' },
  { id: 'generate', label: 'Generating prosecution brief', status: 'pending' },
  { id: 'defense',  label: 'Generating defense brief', status: 'pending' },
  { id: 'verify',   label: 'Verifying citations', status: 'pending' },
]

export default function FactConfirmation({ facts: initialFacts, onBriefGenerated }: FactConfirmationProps) {
  const navigate = useNavigate()
  const [facts, setFacts] = useState<ExtractedFacts | null>(initialFacts)
  const [loading, setLoading] = useState(false)
  const [steps, setSteps] = useState<Step[]>(INITIAL_STEPS)
  const [error, setError] = useState<string | null>(null)

  if (!facts) {
    return (
      <main className="page" id="fact-confirmation-page">
        <div className="container" style={{ padding: 'var(--space-16)', textAlign: 'center' }}>
          <p style={{ opacity: 0.5 }}>No case loaded yet — paste the facts to begin.</p>
          <button className="btn btn-primary" onClick={() => navigate('/intake')} style={{ marginTop: 'var(--space-6)' }}>
            Go to intake
          </button>
        </div>
      </main>
    )
  }

  const setStepStatus = (id: string, status: Step['status']) => {
    setSteps(prev => prev.map(s => s.id === id ? { ...s, status } : s))
  }

  const updateFact = (key: keyof ExtractedFacts, value: string) => {
    setFacts(prev => prev ? { ...prev, [key]: value } : prev)
  }

  const handleConfirm = async () => {
    if (!facts) return
    setLoading(true)
    setError(null)
    setSteps(INITIAL_STEPS)

    try {
      // Step 1: Retrieve
      setStepStatus('retrieve', 'active')
      const { sections } = await retrieveSections(facts)
      setStepStatus('retrieve', 'done')

      // Step 2 + 3: Generate briefs (parallel internally)
      setStepStatus('generate', 'active')
      setStepStatus('defense', 'active')
      const brief = await generateBriefs(facts, sections)
      setStepStatus('generate', 'done')
      setStepStatus('defense', 'done')

      // Step 4: Verify (already done server-side)
      setStepStatus('verify', 'active')
      await new Promise(r => setTimeout(r, 300))  // small visual delay
      setStepStatus('verify', 'done')

      onBriefGenerated(brief, facts)
      navigate('/results')
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Check your case details and try again.')
      setSteps(prev => prev.map(s => s.status === 'active' ? { ...s, status: 'error' } : s))
    } finally {
      setLoading(false)
    }
  }

  const codeEraLabel = facts.code_era === 'old'
    ? 'IPC / CrPC / Evidence Act (offence before 1 July 2024)'
    : facts.code_era === 'new'
    ? 'BNS / BNSS / BSA (offence on or after 1 July 2024)'
    : 'Undetermined — defaulting to new code'

  return (
    <main className="page" id="fact-confirmation-page">
      <div className="container" style={{ maxWidth: 900, margin: '0 auto', padding: 'var(--space-12) var(--space-8)' }}>

        <div style={{ marginBottom: 'var(--space-8)' }}>
          <p className="hero-kicker">Step 2 of 3</p>
          <h1 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-3)' }}>
            Confirm extracted facts.
          </h1>
          <p style={{ fontSize: 'var(--text-sm)', opacity: 0.6 }}>
            Review and correct any field before retrieval runs. Extraction errors compound downstream.
          </p>
        </div>

        {/* Code era indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            padding: 'var(--space-3) var(--space-4)',
            background: 'rgba(27, 42, 74, 0.5)',
            border: '1px solid var(--border-brass)',
            borderRadius: 3,
            marginBottom: 'var(--space-6)',
            fontSize: 'var(--text-xs)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <span style={{ color: 'var(--brass)' }}>CODE ERA:</span>
          <span style={{ opacity: 0.8 }}>{codeEraLabel}</span>
        </div>

        {/* Fact fields */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: 'var(--space-4)',
            marginBottom: 'var(--space-8)',
          }}
        >
          {([
            ['offence_type', 'Offence type'],
            ['intent', 'Intent / mens rea'],
            ['weapon_or_method', 'Weapon / method'],
            ['injury', 'Injury / harm'],
            ['relationship', 'Relationship (accused ↔ victim)'],
            ['location', 'Location'],
          ] as [keyof ExtractedFacts, string][]).map(([key, label]) => (
            <div key={key} className="fact-chip">
              <div className="fact-chip-label">{label}</div>
              <input
                id={`fact-${key}`}
                type="text"
                value={(facts[key] as string) || ''}
                onChange={e => updateFact(key, e.target.value)}
                style={{
                  background: 'none',
                  border: 'none',
                  outline: 'none',
                  color: 'var(--parchment)',
                  fontFamily: 'var(--font-body)',
                  fontSize: 'var(--text-sm)',
                  width: '100%',
                  padding: 0,
                }}
                placeholder="(not extracted — add manually)"
              />
            </div>
          ))}
        </div>

        {/* Evidence list */}
        <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="fact-chip-label" style={{ marginBottom: 'var(--space-3)' }}>Evidence available</div>
          {(facts.evidence_available.length > 0) ? (
            <ul style={{ listStyle: 'none', display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
              {facts.evidence_available.map((e, i) => (
                <li key={i} style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 'var(--text-xs)',
                  background: 'rgba(212,162,76,0.08)',
                  border: '1px solid rgba(212,162,76,0.2)',
                  borderRadius: 2,
                  padding: '0.2rem 0.5rem',
                  color: 'var(--parchment)',
                  opacity: 0.8,
                }}>
                  {e}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ fontSize: 'var(--text-sm)', opacity: 0.4 }}>No evidence items extracted.</p>
          )}
        </div>

        {/* Progress stepper (shows during loading) */}
        {loading && (
          <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
            <ProgressStepper steps={steps} />
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            role="alert"
            style={{
              background: 'rgba(122, 46, 46, 0.15)',
              border: '1px solid rgba(122, 46, 46, 0.4)',
              borderRadius: 3,
              padding: 'var(--space-3)',
              fontSize: 'var(--text-sm)',
              color: '#E07070',
              marginBottom: 'var(--space-4)',
            }}
          >
            {error}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
          <button
            className="btn btn-ghost"
            id="fact-back"
            onClick={() => navigate('/intake')}
            disabled={loading}
          >
            ← Edit narrative
          </button>
          <button
            className="btn btn-primary"
            id="fact-confirm"
            onClick={handleConfirm}
            disabled={loading}
            style={{ flex: 1, justifyContent: 'center' }}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: 16, height: 16 }} />
                Generating both briefs…
              </>
            ) : (
              'Confirm and generate both briefs →'
            )}
          </button>
        </div>
      </div>
    </main>
  )
}
