import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { signInWithEmail, signUpWithEmail } from '../services/supabase'

export default function Auth() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'signin' | 'signup'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setInfo(null)
    setLoading(true)

    try {
      if (mode === 'signin') {
        const { error: err } = await signInWithEmail(email, password)
        if (err) throw err
        navigate('/intake')
      } else {
        const { error: err } = await signUpWithEmail(email, password)
        if (err) throw err
        setInfo('Account created. Check your email to confirm, then sign in.')
        setMode('signin')
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page" id="auth-page">
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 'var(--space-16) var(--space-8)',
        }}
      >
        <div
          style={{
            width: '100%',
            maxWidth: 420,
            background: 'var(--surface-card)',
            border: '1px solid var(--border-brass)',
            borderRadius: 4,
            padding: 'var(--space-8)',
          }}
        >
          {/* Logo + title */}
          <div style={{ textAlign: 'center', marginBottom: 'var(--space-8)' }}>
            <img src="/logo.png" alt="Nyaya Tarazu" style={{ height: 52, marginBottom: 'var(--space-4)' }} />
            <h1 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-2)' }}>
              {mode === 'signin' ? 'Sign in' : 'Create an account'}
            </h1>
            <p style={{ fontSize: 'var(--text-sm)', opacity: 0.5 }}>
              Case data is sensitive. Authentication is required.
            </p>
          </div>

          {/* Error / info */}
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
          {info && (
            <div
              role="status"
              style={{
                background: 'rgba(212, 162, 76, 0.1)',
                border: '1px solid rgba(212, 162, 76, 0.3)',
                borderRadius: 3,
                padding: 'var(--space-3)',
                fontSize: 'var(--text-sm)',
                color: 'var(--brass)',
                marginBottom: 'var(--space-4)',
              }}
            >
              {info}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} id="auth-form">
            <div className="field-group">
              <label htmlFor="auth-email" className="field-label">Email</label>
              <input
                id="auth-email"
                type="email"
                className="input"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="field-group" style={{ marginBottom: 'var(--space-6)' }}>
              <label htmlFor="auth-password" className="field-label">Password</label>
              <input
                id="auth-password"
                type="password"
                className="input"
                placeholder={mode === 'signup' ? 'Min 6 characters' : '••••••••'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              id="auth-submit"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {loading ? (
                <>
                  <div className="spinner" style={{ width: 16, height: 16 }} />
                  {mode === 'signin' ? 'Signing in…' : 'Creating account…'}
                </>
              ) : (
                mode === 'signin' ? 'Sign in' : 'Create account'
              )}
            </button>
          </form>

          {/* Toggle mode */}
          <p style={{ textAlign: 'center', marginTop: 'var(--space-6)', fontSize: 'var(--text-sm)', opacity: 0.6 }}>
            {mode === 'signin' ? "Don't have an account? " : 'Already have an account? '}
            <button
              id="auth-toggle"
              onClick={() => { setMode(mode === 'signin' ? 'signup' : 'signin'); setError(null) }}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--saffron)',
                cursor: 'pointer',
                fontSize: 'inherit',
                padding: 0,
                fontFamily: 'inherit',
              }}
            >
              {mode === 'signin' ? 'Create one' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </main>
  )
}
