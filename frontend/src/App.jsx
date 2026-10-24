import React, { useState, useEffect } from 'react';
import { api } from './api';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

// Pages
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Predict from './pages/Predict';
import Result from './pages/Result';
import History from './pages/History';
import PredictionDetail from './pages/PredictionDetail';
import Analytics from './pages/Analytics';
import Performance from './pages/Performance';
import Recommendations from './pages/Recommendations';
import Import from './pages/Import';
import Login from './pages/Login';
import Register from './pages/Register';
import Methodology from './pages/Methodology';
import About from './pages/About';

import { RefreshCw, AlertCircle, CheckCircle2, Info } from 'lucide-react';

export default function App() {
  const [currentCompany, setCurrentCompany] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [currentPage, setCurrentPage] = useState('home');
  const [pageParams, setPageParams] = useState({});
  const [alert, setAlert] = useState(null);

  // Initial Auth Check on Mount
  useEffect(() => {
    async function checkAuth() {
      try {
        const res = await api.getAuthMe();
        if (res.authenticated && res.company) {
          setCurrentCompany(res.company);
          setCurrentPage('dashboard');
        } else {
          setCurrentCompany(null);
          setCurrentPage('home');
        }
      } catch (err) {
        console.warn('Auth check failed:', err);
        setCurrentCompany(null);
        setCurrentPage('home');
      } finally {
        setAuthChecking(false);
      }
    }
    checkAuth();
  }, []);

  // Central Navigation Handler
  const navigate = (page, params = {}) => {
    const protectedPages = [
      'dashboard',
      'history',
      'prediction_detail',
      'analytics',
      'performance',
      'recommendations',
      'import',
    ];

    if (protectedPages.includes(page) && !currentCompany) {
      setAlert({
        type: 'warning',
        message: 'Please sign in or register your company to access this workspace section.',
      });
      setCurrentPage('login');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setCurrentPage(page);
    setPageParams(params);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLoginSuccess = (company) => {
    setCurrentCompany(company);
    setAlert({
      type: 'success',
      message: `Welcome back to ${company.name} workspace!`,
    });
    setTimeout(() => setAlert(null), 5000);
    navigate('dashboard');
  };

  const handleRegisterSuccess = (company) => {
    setCurrentCompany(company);
    setAlert({
      type: 'success',
      message: `Company workspace for "${company.name}" created successfully.`,
    });
    setTimeout(() => setAlert(null), 5000);
    navigate('dashboard');
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.warn('Logout error', err);
    } finally {
      setCurrentCompany(null);
      setPageParams({});
      setAlert({
        type: 'info',
        message: 'You have been signed out of your company workspace.',
      });
      setTimeout(() => setAlert(null), 4000);
      navigate('home');
    }
  };

  if (authChecking) {
    return (
      <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-page)' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="animate-spin" style={{ display: 'inline-block', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
            <RefreshCw size={32} />
          </div>
          <div style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
            Initializing ReturnRisk Platform...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-layout">
      <Navbar
        currentCompany={currentCompany}
        currentPage={currentPage}
        onNavigate={navigate}
        onLogout={handleLogout}
      />

      {/* Global Alert Notification Banner */}
      {alert && (
        <div className="container" style={{ marginTop: '1.25rem' }}>
          <div
            className={`callout ${alert.type === 'danger' ? 'callout-danger' : ''}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 0,
              backgroundColor: alert.type === 'success' ? 'var(--accent-light)' : undefined,
              borderColor: alert.type === 'success' ? 'var(--accent-border)' : undefined,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {alert.type === 'success' && <CheckCircle2 size={16} color="var(--accent-primary)" />}
              {alert.type === 'danger' && <AlertCircle size={16} color="var(--risk-high-accent)" />}
              {alert.type === 'warning' && <AlertCircle size={16} color="var(--risk-mod-accent)" />}
              {alert.type === 'info' && <Info size={16} color="var(--accent-primary)" />}
              <span style={{ fontSize: '0.88rem' }}>{alert.message}</span>
            </div>
            <button
              onClick={() => setAlert(null)}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1rem' }}
            >
              &times;
            </button>
          </div>
        </div>
      )}

      <main className="main-content">
        <div className="container">
          {/* Page Routing */}
          {currentPage === 'home' && (
            <Home currentCompany={currentCompany} onNavigate={navigate} />
          )}

          {currentPage === 'dashboard' && currentCompany && (
            <Dashboard currentCompany={currentCompany} onNavigate={navigate} />
          )}

          {currentPage === 'predict' && (
            <Predict
              onResult={(res) => navigate('result', { result: res })}
              onNavigate={navigate}
            />
          )}

          {currentPage === 'result' && (
            <Result
              result={pageParams.result}
              onNavigate={navigate}
            />
          )}

          {currentPage === 'history' && (
            <History onNavigate={navigate} />
          )}

          {currentPage === 'prediction_detail' && (
            <PredictionDetail
              predictionId={pageParams.id}
              onNavigate={navigate}
            />
          )}

          {currentPage === 'analytics' && (
            <Analytics onNavigate={navigate} />
          )}

          {currentPage === 'performance' && (
            <Performance onNavigate={navigate} />
          )}

          {currentPage === 'recommendations' && (
            <Recommendations onNavigate={navigate} />
          )}

          {currentPage === 'import' && (
            <Import onNavigate={navigate} />
          )}

          {currentPage === 'login' && (
            <Login
              onLoginSuccess={handleLoginSuccess}
              onNavigate={navigate}
            />
          )}

          {currentPage === 'register' && (
            <Register
              onRegisterSuccess={handleRegisterSuccess}
              onNavigate={navigate}
            />
          )}

          {currentPage === 'methodology' && (
            <Methodology onNavigate={navigate} />
          )}

          {currentPage === 'about' && (
            <About onNavigate={navigate} />
          )}
        </div>
      </main>

      <Footer onNavigate={navigate} />
    </div>
  );
}
