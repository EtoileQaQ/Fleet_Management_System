import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';
import { Zap, Mail, Lock, AlertCircle, Loader2 } from 'lucide-react';
import './Login.css';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSetup, setIsSetup] = useState(false);
  
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let tokens;
      
      if (isSetup) {
        await authApi.setup(email, password);
        tokens = await authApi.login(email, password);
      } else {
        tokens = await authApi.login(email, password);
      }
      
      // Save tokens FIRST so getCurrentUser can use them
      useAuthStore.getState().setTokens(tokens.access_token, tokens.refresh_token);
      
      const user = await authApi.getCurrentUser();
      login(user, tokens.access_token, tokens.refresh_token);
      navigate('/');
    } catch (err) {
      if (err.response?.status === 400 && err.response?.data?.detail?.includes('Setup already')) {
        setIsSetup(false);
        setError('Setup already completed. Please login.');
      } else if (err.response?.status === 401) {
        setError('Invalid email or password');
      } else {
        setError(err.response?.data?.detail || 'An error occurred. Try setup if this is your first time.');
        if (!isSetup) {
          setIsSetup(true);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* Background decoration */}
      <div className="login-bg">
        <div className="login-bg-gradient"></div>
        <div className="login-bg-grid"></div>
      </div>

      <div className="login-container">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">
            <Zap size={32} />
          </div>
          <h1>FleetPulse</h1>
          <p>Fleet Management System</p>
        </div>

        {/* Login Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-header">
            <h2>{isSetup ? 'Create Admin Account' : 'Welcome Back'}</h2>
            <p>
              {isSetup 
                ? 'Set up your first admin account to get started' 
                : 'Sign in to manage your fleet'}
            </p>
          </div>

          {error && (
            <div className="login-error animate-fade-in">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email address</label>
            <div className="input-wrapper">
              <Mail size={18} className="input-icon" />
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@example.com"
                required
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <Lock size={18} className="input-icon" />
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                <span>{isSetup ? 'Creating...' : 'Signing in...'}</span>
              </>
            ) : (
              <span>{isSetup ? 'Create Account' : 'Sign In'}</span>
            )}
          </button>

          <button
            type="button"
            className="toggle-mode-btn"
            onClick={() => {
              setIsSetup(!isSetup);
              setError('');
            }}
          >
            {isSetup ? 'Already have an account? Sign in' : 'First time? Set up admin account'}
          </button>
        </form>

        {/* Footer */}
        <div className="login-footer">
          <p>Secure fleet management for your business</p>
        </div>
      </div>
    </div>
  );
}

export default Login;



