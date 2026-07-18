import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { extractFacts, type ExtractedFacts } from '../services/api'

interface CaseIntakeProps {
  onFactsExtracted: (facts: ExtractedFacts) => void
}

export default function CaseIntake({ onFactsExtracted }: CaseIntakeProps) {
  const navigate = useNavigate()
  const [narrative, setNarrative] = useState('')
  const [offenceDate, setOffenceDate] = useState('')
  const [location, setLocation] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (narrative.trim().length < 20) {
      setError("Couldn't find enough case detail here. Try adding who did what, and when.")
      return
    }
    setError(null)
    setLoading(true)
    try {
      const facts = await extractFacts(narrative, offenceDate || null)
      onFactsExtracted(facts)
      navigate('/confirm')
    } catch (err: any) {
      setError(err.message || 'Fact extraction failed. Try again with more detail.')
    } finally {
      setLoading(false)
    }
  }

  const charCount = narrative.length
  const isReady = charCount >= 20

  return (
    <main className="page" id="case-intake-page">
      <div className="container" style={{ maxWidth: 800, margin: '0 auto', padding: 'var(--space-12) var(--space-8)' }}>

        {/* Header */}
        <div style={{ marginBottom: 'var(--space-8)' }}>
          <p className="hero-kicker" style={{ marginBottom: 'var(--space-3)' }}>New Case</p>
          <h1 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-3)' }}>
            Describe the case facts.
          </h1>
          <p style={{ fontSize: 'var(--text-sm)', opacity: 0.6 }}>
            Write what happened in plain language — who did what, to whom, and when.
            The more detail you give, the more precise the retrieval.
          </p>
        </div>

        <form onSubmit={handleSubmit} id="intake-form">

          {/* Main narrative */}
          <div className="field-group">
            <label htmlFor="intake-narrative" className="field-label">Case narrative *</label>
            <textarea
              id="intake-narrative"
              className="textarea"
              placeholder="e.g. On the night of 15 March 2024, Ramesh Kumar attacked Sita Devi with a knife in her house in Pune, causing grievous hurt. There are two eyewitnesses. The accused fled the scene and was arrested two days later..."
              value={narrative}
              onChange={e => setNarrative(e.target.value)}
              style={{ minHeight: 240 }}
              required
            />
            <div className="field-hint" style={{ textAlign: 'right' }}>
              {charCount} characters {charCount < 20 && '— add more detail'}
            </div>
          </div>

          {/* Optional fields */}
          <div
            style={{
              background: 'var(--surface-card-alt)',
              border: '1px solid var(--border-brass)',
              borderRadius: 3,
              padding: 'var(--space-4)',
              marginBottom: 'var(--space-6)',
            }}
          >
            <p style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: 'var(--brass)', letterSpacing: '0.1em', marginBottom: 'var(--space-4)', textTransform: 'uppercase' }}>
              Optional — helps with retrieval
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
              <div className="field-group" style={{ marginBottom: 0 }}>
                <label htmlFor="intake-date" className="field-label">Offence date</label>
                <input
                  id="intake-date"
                  type="date"
                  className="input"
                  value={offenceDate}
                  onChange={e => setOffenceDate(e.target.value)}
                />
                <p className="field-hint">
                  Before 1 July 2024 → IPC/CrPC. After → BNS/BNSS/BSA.
                </p>
              </div>
              <div className="field-group" style={{ marginBottom: 0 }}>
                <label htmlFor="intake-location" className="field-label">Location / State</label>
                <input
                  id="intake-location"
                  type="text"
                  className="input"
                  placeholder="e.g. Mumbai, Maharashtra"
                  value={location}
                  onChange={e => setLocation(e.target.value)}
                />
              </div>
            </div>
          </div>

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

          {/* Submit */}
          <button
            type="submit"
            className="btn btn-primary"
            id="intake-submit"
            disabled={loading || !isReady}
            style={{ width: '100%', justifyContent: 'center', fontSize: 'var(--text-sm)' }}
          >
            {loading ? (
              <>
                <div className="spinner" style={{ width: 16, height: 16 }} />
                Extracting facts…
              </>
            ) : (
              'Extract facts →'
            )}
          </button>
        </form>
      </div>
    </main>
  )
}
