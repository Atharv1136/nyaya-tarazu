import { Link, NavLink } from 'react-router-dom'

interface NavbarProps {
  isAuthenticated?: boolean
  onLogout?: () => void
}

export default function Navbar({ isAuthenticated, onLogout }: NavbarProps) {
  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="container">
        {/* Brand / Logo */}
        <Link to="/" className="navbar-brand" id="nav-brand">
          <img
            src="/logo.png"
            alt="Nyaya Tarazu logo — scales of justice"
            className="navbar-logo"
          />
          <span className="navbar-wordmark">
            <span>Nyaya</span>Tarazu
          </span>
        </Link>

        {/* Navigation links */}
        <ul className="navbar-links" role="list">
          <li>
            <NavLink
              to="/"
              id="nav-home"
              className={({ isActive }) => isActive ? 'active' : ''}
              end
            >
              Home
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/lookup"
              id="nav-lookup"
              className={({ isActive }) => isActive ? 'active' : ''}
            >
              Lookup
            </NavLink>
          </li>
          {isAuthenticated ? (
            <>
              <li>
                <NavLink
                  to="/intake"
                  id="nav-intake"
                  className={({ isActive }) => isActive ? 'active' : ''}
                >
                  New Case
                </NavLink>
              </li>
              <li>
                <button
                  className="btn btn-ghost"
                  id="nav-logout"
                  onClick={onLogout}
                  style={{ padding: '0.5rem 1rem', fontSize: 'var(--text-xs)' }}
                >
                  Sign out
                </button>
              </li>
            </>
          ) : (
            <li>
              <Link to="/auth" id="nav-login">
                <button className="btn btn-primary" style={{ padding: '0.5rem 1.25rem', fontSize: 'var(--text-xs)' }}>
                  Sign in
                </button>
              </Link>
            </li>
          )}
        </ul>
      </div>
    </nav>
  )
}
