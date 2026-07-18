import { useState, useRef } from 'react'
import { lookupSection, type LookupResponse } from '../services/api'
import CitationChip from '../components/CitationChip'

interface Message {
  id: string
  role: 'user' | 'assistant'
  text: string
  response?: LookupResponse
}

export default function SectionLookup() {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const sendQuestion = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || loading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: question.trim(),
    }
    setMessages(prev => [...prev, userMsg])
    setQuestion('')
    setError(null)
    setLoading(true)

    try {
      const resp = await lookupSection(question.trim())
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        text: resp.answer,
        response: resp,
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err: any) {
      setError(err.message || 'Lookup failed.')
    } finally {
      setLoading(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    }
  }

  const exampleQuestions = [
    'What is the BNS equivalent of IPC 302?',
    'What constitutes "grievous hurt" under BNS?',
    'CrPC 161 and its BNSS equivalent?',
    'What are the sections for cheating under IPC?',
  ]

  return (
    <main className="page" id="section-lookup-page">
      <div className="container" style={{ maxWidth: 860, margin: '0 auto', padding: 'var(--space-8) var(--space-8)' }}>

        {/* Header */}
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <p className="hero-kicker">Section Lookup</p>
          <h1 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-2)' }}>
            Ask a direct statute question.
          </h1>
          <p style={{ fontSize: 'var(--text-sm)', opacity: 0.6 }}>
            "What is the BNS equivalent of IPC 302?" · "What does BSA §65 cover?" · "Punishment for dacoity under BNSS?"
          </p>
        </div>

        {/* Terminal */}
        <div className="lookup-terminal" id="lookup-terminal">

          {/* Messages */}
          <div className="lookup-messages">
            {messages.length === 0 && !loading && (
              <div style={{ textAlign: 'center', padding: 'var(--space-8) 0', opacity: 0.4 }}>
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', marginBottom: 'var(--space-4)' }}>
                  — No queries yet —
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', justifyContent: 'center' }}>
                  {exampleQuestions.map(q => (
                    <button
                      key={q}
                      onClick={() => setQuestion(q)}
                      style={{
                        background: 'rgba(212,162,76,0.06)',
                        border: '1px solid rgba(212,162,76,0.2)',
                        borderRadius: 2,
                        color: 'var(--parchment)',
                        opacity: 0.7,
                        fontSize: 'var(--text-xs)',
                        fontFamily: 'var(--font-mono)',
                        padding: '0.3rem 0.6rem',
                        cursor: 'pointer',
                        textAlign: 'left',
                      }}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map(msg => (
              <div
                key={msg.id}
                className={`lookup-message ${msg.role}`}
                id={`msg-${msg.id}`}
              >
                {msg.role === 'user' ? (
                  <span>{msg.text}</span>
                ) : (
                  <div>
                    <p style={{ marginBottom: 'var(--space-3)', lineHeight: 1.7 }}>{msg.text}</p>

                    {/* Cited sections */}
                    {msg.response && msg.response.cited_sections.length > 0 && (
                      <div style={{ marginTop: 'var(--space-3)' }}>
                        <div style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 'var(--text-xs)',
                          color: 'var(--brass)',
                          opacity: 0.6,
                          marginBottom: 'var(--space-2)',
                          letterSpacing: '0.1em',
                          textTransform: 'uppercase',
                        }}>
                          Source sections
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {msg.response.cited_sections.slice(0, 6).map(s => (
                            <CitationChip
                              key={s.chunk_id}
                              citation={`${s.act_name.split(',')[0]} §${s.section_number || '?'}`}
                              verified
                              previewText={s.chunk_text.slice(0, 200)}
                            />
                          ))}
                        </div>

                        {/* Cross-references */}
                        {msg.response.cross_references.length > 0 && (
                          <div style={{ marginTop: 'var(--space-2)', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                            <span style={{ fontSize: 'var(--text-xs)', opacity: 0.4, fontFamily: 'var(--font-mono)' }}>
                              XREF:
                            </span>
                            {msg.response.cross_references.slice(0, 4).map(ref => (
                              <span key={ref} style={{
                                fontFamily: 'var(--font-mono)',
                                fontSize: 'var(--text-xs)',
                                color: 'rgba(232,225,211,0.5)',
                              }}>
                                {ref}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="lookup-message assistant">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, opacity: 0.5 }}>
                  <div className="spinner" style={{ width: 14, height: 14 }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>
                    Searching corpus…
                  </span>
                </div>
              </div>
            )}

            {error && (
              <div role="alert" style={{
                padding: 'var(--space-3)',
                background: 'rgba(122,46,46,0.15)',
                border: '1px solid rgba(122,46,46,0.4)',
                borderRadius: 3,
                fontSize: 'var(--text-sm)',
                color: '#E07070',
              }}>
                {error}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input row */}
          <form className="lookup-input-row" onSubmit={sendQuestion} id="lookup-form">
            <input
              id="lookup-input"
              type="text"
              className="input"
              placeholder="Ask a statute question…"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <button
              type="submit"
              className="btn btn-primary"
              id="lookup-submit"
              disabled={loading || !question.trim()}
              style={{ whiteSpace: 'nowrap' }}
            >
              {loading ? <div className="spinner" style={{ width: 16, height: 16 }} /> : 'Ask →'}
            </button>
          </form>
        </div>

        {/* Help text */}
        <p style={{ fontSize: 'var(--text-xs)', opacity: 0.4, marginTop: 'var(--space-4)', fontFamily: 'var(--font-mono)' }}>
          Searches both old (IPC/CrPC/Evidence Act) and new (BNS/BNSS/BSA) code corpus simultaneously.
        </p>
      </div>
    </main>
  )
}
