import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Auth from './pages/Auth'
import CaseIntake from './pages/CaseIntake'
import FactConfirmation from './pages/FactConfirmation'
import Results from './pages/Results'
import SectionLookup from './pages/SectionLookup'
import type { ExtractedFacts, BriefResponse } from './services/api'
import { supabase, signOut } from './services/supabase'
import type { Session } from '@supabase/supabase-js'

export default function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [sessionLoading, setSessionLoading] = useState(true)

  // App-level state (pass-through between intake → confirm → results)
  const [extractedFacts, setExtractedFacts] = useState<ExtractedFacts | null>(null)
  const [briefResponse, setBriefResponse] = useState<BriefResponse | null>(null)
  const [briefFacts, setBriefFacts] = useState<ExtractedFacts | null>(null)

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setSessionLoading(false)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })
    return () => subscription.unsubscribe()
  }, [])

  const handleLogout = async () => {
    await signOut()
    setSession(null)
    setExtractedFacts(null)
    setBriefResponse(null)
    setBriefFacts(null)
  }

  const handleBriefGenerated = (brief: BriefResponse, facts: ExtractedFacts) => {
    setBriefResponse(brief)
    setBriefFacts(facts)
  }

  if (sessionLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'var(--ink)',
      }}>
        <div className="spinner" />
      </div>
    )
  }

  const isAuthenticated = !!session

  return (
    <BrowserRouter>
      <Navbar isAuthenticated={isAuthenticated} onLogout={handleLogout} />
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Landing />} />
        <Route
          path="/auth"
          element={isAuthenticated ? <Navigate to="/intake" replace /> : <Auth />}
        />
        <Route path="/lookup" element={<SectionLookup />} />

        {/* Protected routes */}
        <Route
          path="/intake"
          element={
            isAuthenticated
              ? <CaseIntake onFactsExtracted={setExtractedFacts} />
              : <Navigate to="/auth" replace />
          }
        />
        <Route
          path="/confirm"
          element={
            isAuthenticated
              ? <FactConfirmation facts={extractedFacts} onBriefGenerated={handleBriefGenerated} />
              : <Navigate to="/auth" replace />
          }
        />
        <Route
          path="/results"
          element={
            isAuthenticated
              ? <Results brief={briefResponse} facts={briefFacts} />
              : <Navigate to="/auth" replace />
          }
        />

        {/* 404 fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
