import { Link } from 'react-router-dom'
import ScaleHero from '../components/ScaleHero'

export default function Landing() {
  return (
    <main className="page" id="landing-page">
      <div className="container">

        {/* ===== HERO ===== */}
        <section className="hero" aria-label="Hero section">
          {/* Left: headline + CTA */}
          <div className="hero-content fade-up">
            <p className="hero-kicker">Indian Criminal Law · BNS · IPC · BNSS · CrPC</p>
            <h1 className="hero-title">
              Weigh <em>both sides.</em><br />
              Ground every argument.
            </h1>
            <p className="hero-subtitle">
              Paste a case. Get two real, cited legal briefs — prosecution and defense —
              grounded in verified sections of Indian criminal law. Not a chatbot. A drafting tool.
            </p>
            <div className="hero-actions">
              <Link to="/intake" id="hero-cta-start">
                <button className="btn btn-primary" style={{ fontSize: 'var(--text-sm)' }}>
                  Start a case
                </button>
              </Link>
              <a href="#how-it-works" id="hero-cta-how">
                <button className="btn btn-secondary" style={{ fontSize: 'var(--text-sm)' }}>
                  See how it works
                </button>
              </a>
            </div>
          </div>

          {/* Right: 3D scale */}
          <ScaleHero />
        </section>

        {/* ===== HOW IT WORKS — split section ===== */}
        <section id="how-it-works" aria-label="How Nyaya Tarazu works">
          <div className="section-divider">
            <span className="section-divider-label">How it works</span>
          </div>

          <div className="split-section" style={{ minHeight: 480 }}>
            {/* Prosecution side */}
            <div className="split-prosecution">
              <p className="split-label">Prosecution</p>
              <h2 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-4)', fontFamily: 'var(--font-display)' }}>
                Build the strongest case for the state.
              </h2>
              <p style={{ fontSize: 'var(--text-sm)', opacity: 0.75, lineHeight: 1.7, marginBottom: 'var(--space-4)' }}>
                Nyaya Tarazu retrieves the most relevant statutory sections and constructs
                a prosecution brief — issues, applicable provisions, arguments, and prayer —
                grounded only in verified text from BNS, BNSS, BSA, IPC, CrPC, and the Evidence Act.
              </p>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--saffron)', opacity: 0.7 }}>
                Every §citation is verified against the corpus.
              </div>
            </div>

            {/* Defense side */}
            <div className="split-defense">
              <p className="split-label">Defense</p>
              <h2 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-4)', fontFamily: 'var(--font-display)' }}>
                Challenge every element of the charge.
              </h2>
              <p style={{ fontSize: 'var(--text-sm)', opacity: 0.75, lineHeight: 1.7, marginBottom: 'var(--space-4)' }}>
                Simultaneously, a parallel LLM call argues the defense — probing intent,
                testing the burden of proof, citing exceptions and precedents. The same facts,
                weighed from the other side of the scale.
              </p>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--brass)', opacity: 0.7 }}>
                Unverifiable citations are flagged, not hidden.
              </div>
            </div>
          </div>
        </section>

        {/* ===== PIPELINE STEPS ===== */}
        <section aria-label="Pipeline steps" style={{ margin: 'var(--space-24) 0' }}>
          <div className="section-divider">
            <span className="section-divider-label">The pipeline</span>
          </div>

          {[
            {
              n: '01',
              title: 'Intake',
              desc: 'Paste the case facts in plain language. Include who did what, when, and where. The system determines which code applies based on the offence date.',
            },
            {
              n: '02',
              title: 'Fact Extraction',
              desc: 'Gemini structures the narrative into parties, offence type, intent, weapon/method, injury, relationship, and evidence. Every field is editable before retrieval runs.',
            },
            {
              n: '03',
              title: 'Hybrid Retrieval',
              desc: 'BM25 keyword search + pgvector cosine similarity against 270+ sections of Indian law, fused with Reciprocal Rank Fusion. Routed to old (IPC/CrPC) or new (BNS/BNSS/BSA) corpus.',
            },
            {
              n: '04',
              title: 'Dual Brief Generation',
              desc: 'Two parallel LLM calls — prosecution persona and defense persona — each grounded only in the retrieved sections. Structured output: issues, provisions, arguments, precedents, prayer.',
            },
            {
              n: '05',
              title: 'Citation Verification + Export',
              desc: 'Every §citation is checked against the retrieval corpus. Unverifiable citations are flagged inline. Export either brief as a Word document in courtroom-drafting format.',
            },
          ].map((step) => (
            <div key={step.n} className="feature-row">
              <div className="feature-number">{step.n}</div>
              <div>
                <h3 style={{ fontSize: 'var(--text-base)', marginBottom: 'var(--space-2)' }}>
                  {step.title}
                </h3>
                <p style={{ fontSize: 'var(--text-sm)', opacity: 0.7, lineHeight: 1.65 }}>
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </section>

        {/* ===== FINAL CTA ===== */}
        <section
          aria-label="Get started"
          style={{
            textAlign: 'center',
            padding: 'var(--space-16) 0',
            borderTop: '1px solid var(--border-brass)',
          }}
        >
          <h2 style={{ fontSize: 'var(--text-xl)', marginBottom: 'var(--space-4)' }}>
            Ready to draft both sides?
          </h2>
          <p style={{ opacity: 0.6, marginBottom: 'var(--space-8)', fontSize: 'var(--text-sm)' }}>
            No account required to explore — sign in when you paste your first case.
          </p>
          <Link to="/auth" id="landing-bottom-cta">
            <button className="btn btn-primary">
              Create an account
            </button>
          </Link>
        </section>

      </div>

      {/* ===== FOOTER ===== */}
      <footer className="footer">
        <div className="container">
          <div className="footer-grid">
            <div className="footer-brand">
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
                <img src="/logo.png" alt="Nyaya Tarazu" style={{ height: 32 }} />
                <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700 }}>Nyaya Tarazu</span>
              </div>
              <p>Weigh. Analyze. Draft. Argue.</p>
              <p style={{ marginTop: 'var(--space-2)', fontSize: 'var(--text-xs)', opacity: 0.4 }}>
                AI-generated drafts. Always verify before use in any proceeding.
              </p>
            </div>
            <div>
              <div className="footer-heading">Product</div>
              <ul className="footer-links">
                <li><Link to="/intake">Start a case</Link></li>
                <li><Link to="/lookup">Section lookup</Link></li>
                <li><Link to="/auth">Sign in</Link></li>
              </ul>
            </div>
            <div>
              <div className="footer-heading">Law corpus</div>
              <ul className="footer-links">
                <li><span style={{ fontSize: 'var(--text-xs)', opacity: 0.5 }}>BNS 2023</span></li>
                <li><span style={{ fontSize: 'var(--text-xs)', opacity: 0.5 }}>BNSS 2023</span></li>
                <li><span style={{ fontSize: 'var(--text-xs)', opacity: 0.5 }}>BSA 2023</span></li>
                <li><span style={{ fontSize: 'var(--text-xs)', opacity: 0.5 }}>IPC 1860</span></li>
                <li><span style={{ fontSize: 'var(--text-xs)', opacity: 0.5 }}>CrPC 1973</span></li>
                <li><span style={{ fontSize: 'var(--text-xs)', opacity: 0.5 }}>Evidence Act 1872</span></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <span>© 2026 Nyaya Tarazu. For professional use by licensed advocates only.</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem' }}>v1.0.0</span>
          </div>
        </div>
      </footer>
    </main>
  )
}
