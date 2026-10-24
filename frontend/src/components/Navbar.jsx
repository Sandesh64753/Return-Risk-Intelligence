import React, { useState, useEffect, useRef } from 'react';
import {
  LayoutDashboard,
  Cpu,
  History,
  BarChart3,
  TrendingDown,
  Lightbulb,
  UploadCloud,
  BookOpen,
  LogOut,
  LogIn,
  UserPlus,
  Menu,
  X,
  ChevronDown
} from 'lucide-react';

export default function Navbar({ currentCompany, currentPage, onNavigate, onLogout }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  const moreDropdownRef = useRef(null);
  const mobileDrawerRef = useRef(null);

  // Close menus on Escape key
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setMoreOpen(false);
        setMobileOpen(false);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close "More" dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (moreDropdownRef.current && !moreDropdownRef.current.contains(e.target)) {
        setMoreOpen(false);
      }
    }
    if (moreOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [moreOpen]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileOpen]);

  // Central navigation click handler that auto-closes menus
  const handleNav = (page) => {
    onNavigate(page);
    setMoreOpen(false);
    setMobileOpen(false);
  };

  const isMoreActive = ['recommendations', 'import', 'methodology'].includes(currentPage);

  return (
    <header className="site-header">
      <div className="header-container">
        {/* =========================================
            1. Left: Brand Section
           ========================================= */}
        <div className="header-brand-section">
          <a
            href="#dashboard"
            className="brand-wrapper"
            onClick={(e) => {
              e.preventDefault();
              handleNav(currentCompany ? 'dashboard' : 'home');
            }}
            aria-label="ReturnRisk Home"
          >
            <div className="brand-mark" aria-hidden="true">R</div>
            <span className="brand-name">ReturnRisk</span>
            <span className="brand-badge">Intelligence</span>
          </a>
        </div>

        {/* =========================================
            2. Center: Main Navigation (Desktop / Tablet)
           ========================================= */}
        <nav className="header-nav-section" aria-label="Main Navigation">
          {currentCompany ? (
            <div className="header-nav-desktop">
              {/* Primary Routes (always visible on desktop and tablet) */}
              <button
                className={`nav-link ${currentPage === 'dashboard' ? 'active' : ''}`}
                onClick={() => handleNav('dashboard')}
              >
                <LayoutDashboard size={15} />
                <span>Dashboard</span>
              </button>

              <button
                className={`nav-link ${currentPage === 'predict' || currentPage === 'result' ? 'active' : ''}`}
                onClick={() => handleNav('predict')}
              >
                <Cpu size={15} />
                <span>Predict</span>
              </button>

              <button
                className={`nav-link ${currentPage === 'history' || currentPage === 'prediction_detail' ? 'active' : ''}`}
                onClick={() => handleNav('history')}
              >
                <History size={15} />
                <span>History</span>
              </button>

              <button
                className={`nav-link ${currentPage === 'analytics' ? 'active' : ''}`}
                onClick={() => handleNav('analytics')}
              >
                <BarChart3 size={15} />
                <span>Analytics</span>
              </button>

              <button
                className={`nav-link ${currentPage === 'performance' ? 'active' : ''}`}
                onClick={() => handleNav('performance')}
              >
                <TrendingDown size={15} />
                <span>Performance</span>
              </button>

              {/* Secondary Routes: Directly visible on wide desktop (>= 1180px) */}
              <button
                className={`nav-link nav-link-secondary ${currentPage === 'recommendations' ? 'active' : ''}`}
                onClick={() => handleNav('recommendations')}
              >
                <Lightbulb size={15} />
                <span>Recommendations</span>
              </button>

              <button
                className={`nav-link nav-link-secondary ${currentPage === 'import' ? 'active' : ''}`}
                onClick={() => handleNav('import')}
              >
                <UploadCloud size={15} />
                <span>Import</span>
              </button>

              <button
                className={`nav-link nav-link-secondary ${currentPage === 'methodology' ? 'active' : ''}`}
                onClick={() => handleNav('methodology')}
              >
                <BookOpen size={15} />
                <span>Methodology</span>
              </button>

              {/* "More" Dropdown: Activated on tablet widths (860px - 1180px) */}
              <div className="nav-dropdown" ref={moreDropdownRef}>
                <button
                  type="button"
                  className={`nav-link ${isMoreActive ? 'active' : ''}`}
                  onClick={() => setMoreOpen(!moreOpen)}
                  aria-expanded={moreOpen}
                  aria-haspopup="true"
                >
                  <span>More</span>
                  <ChevronDown
                    size={14}
                    style={{
                      transform: moreOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform 0.15s ease'
                    }}
                  />
                </button>

                {moreOpen && (
                  <div className="nav-dropdown-menu" role="menu">
                    <button
                      className={`nav-dropdown-item ${currentPage === 'recommendations' ? 'active' : ''}`}
                      onClick={() => handleNav('recommendations')}
                      role="menuitem"
                    >
                      <Lightbulb size={15} />
                      <span>Recommendations</span>
                    </button>
                    <button
                      className={`nav-dropdown-item ${currentPage === 'import' ? 'active' : ''}`}
                      onClick={() => handleNav('import')}
                      role="menuitem"
                    >
                      <UploadCloud size={15} />
                      <span>Import</span>
                    </button>
                    <button
                      className={`nav-dropdown-item ${currentPage === 'methodology' ? 'active' : ''}`}
                      onClick={() => handleNav('methodology')}
                      role="menuitem"
                    >
                      <BookOpen size={15} />
                      <span>Methodology</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="header-nav-desktop">
              <button
                className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
                onClick={() => handleNav('home')}
              >
                Home
              </button>
              <button
                className={`nav-link ${currentPage === 'methodology' ? 'active' : ''}`}
                onClick={() => handleNav('methodology')}
              >
                Methodology
              </button>
              <button
                className={`nav-link ${currentPage === 'about' ? 'active' : ''}`}
                onClick={() => handleNav('about')}
              >
                About
              </button>
              <a
                href="/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="nav-link"
              >
                API Docs
              </a>
            </div>
          )}
        </nav>

        {/* =========================================
            3. Right: Company Controls / Auth CTA
           ========================================= */}
        <div className="header-actions-section">
          {currentCompany ? (
            <div className="company-profile-group">
              <div
                className="company-pill"
                title={`Logged in as ${currentCompany.name} (${currentCompany.email})`}
              >
                <span className="company-dot" aria-hidden="true"></span>
                <span className="company-name">{currentCompany.name}</span>
              </div>
              <div className="profile-divider" aria-hidden="true"></div>
              <button
                type="button"
                className="btn-logout"
                onClick={onLogout}
                title="Sign out of company workspace"
                aria-label="Logout"
              >
                <LogOut size={14} />
                <span>Logout</span>
              </button>
            </div>
          ) : (
            <div className="auth-cta-group">
              <button
                className={`nav-link ${currentPage === 'login' ? 'active' : ''}`}
                onClick={() => handleNav('login')}
              >
                <LogIn size={15} />
                Sign In
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => handleNav('register')}
              >
                <UserPlus size={14} />
                Register Company
              </button>
            </div>
          )}

          {/* Mobile Menu Hamburger Toggle Button */}
          <button
            type="button"
            className="mobile-menu-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileOpen}
            aria-controls="mobile-navigation-drawer"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* =========================================
          4. Mobile Navigation Drawer & Backdrop
         ========================================= */}
      {mobileOpen && (
        <>
          <div
            className="mobile-backdrop"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <div
            id="mobile-navigation-drawer"
            className="mobile-drawer"
            ref={mobileDrawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Mobile Navigation Drawer"
          >
            <div className="mobile-nav-links">
              {currentCompany ? (
                <>
                  <button
                    className={`mobile-nav-item ${currentPage === 'dashboard' ? 'active' : ''}`}
                    onClick={() => handleNav('dashboard')}
                  >
                    <LayoutDashboard size={18} />
                    <span>Dashboard</span>
                  </button>

                  <button
                    className={`mobile-nav-item ${currentPage === 'predict' || currentPage === 'result' ? 'active' : ''}`}
                    onClick={() => handleNav('predict')}
                  >
                    <Cpu size={18} />
                    <span>Predict</span>
                  </button>

                  <button
                    className={`mobile-nav-item ${currentPage === 'history' || currentPage === 'prediction_detail' ? 'active' : ''}`}
                    onClick={() => handleNav('history')}
                  >
                    <History size={18} />
                    <span>History</span>
                  </button>

                  <button
                    className={`mobile-nav-item ${currentPage === 'analytics' ? 'active' : ''}`}
                    onClick={() => handleNav('analytics')}
                  >
                    <BarChart3 size={18} />
                    <span>Analytics</span>
                  </button>

                  <button
                    className={`mobile-nav-item ${currentPage === 'performance' ? 'active' : ''}`}
                    onClick={() => handleNav('performance')}
                  >
                    <TrendingDown size={18} />
                    <span>Performance</span>
                  </button>

                  <button
                    className={`mobile-nav-item ${currentPage === 'recommendations' ? 'active' : ''}`}
                    onClick={() => handleNav('recommendations')}
                  >
                    <Lightbulb size={18} />
                    <span>Recommendations</span>
                  </button>

                  <button
                    className={`mobile-nav-item ${currentPage === 'import' ? 'active' : ''}`}
                    onClick={() => handleNav('import')}
                  >
                    <UploadCloud size={18} />
                    <span>Import</span>
                  </button>

                  <button
                    className={`mobile-nav-item ${currentPage === 'methodology' ? 'active' : ''}`}
                    onClick={() => handleNav('methodology')}
                  >
                    <BookOpen size={18} />
                    <span>Methodology</span>
                  </button>
                </>
              ) : (
                <>
                  <button
                    className={`mobile-nav-item ${currentPage === 'home' ? 'active' : ''}`}
                    onClick={() => handleNav('home')}
                  >
                    Home
                  </button>
                  <button
                    className={`mobile-nav-item ${currentPage === 'methodology' ? 'active' : ''}`}
                    onClick={() => handleNav('methodology')}
                  >
                    Methodology
                  </button>
                  <button
                    className={`mobile-nav-item ${currentPage === 'about' ? 'active' : ''}`}
                    onClick={() => handleNav('about')}
                  >
                    About
                  </button>
                  <a
                    href="/docs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mobile-nav-item"
                    onClick={() => setMobileOpen(false)}
                  >
                    API Docs
                  </a>
                </>
              )}
            </div>

            {/* Mobile Bottom Profile / Auth Action */}
            <div className="mobile-user-section">
              {currentCompany ? (
                <>
                  <div className="mobile-company-info">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="company-dot" aria-hidden="true"></span>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                          {currentCompany.name}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          {currentCompany.email}
                        </div>
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="mobile-logout-btn"
                    onClick={() => {
                      setMobileOpen(false);
                      onLogout();
                    }}
                  >
                    <LogOut size={16} />
                    <span>Sign Out</span>
                  </button>
                </>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleNav('login')}
                    style={{ width: '100%', justifyContent: 'center' }}
                  >
                    <LogIn size={15} />
                    Sign In
                  </button>
                  <button
                    className="btn btn-primary"
                    onClick={() => handleNav('register')}
                    style={{ width: '100%', justifyContent: 'center' }}
                  >
                    <UserPlus size={15} />
                    Register Company
                  </button>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </header>
  );
}
