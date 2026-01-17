import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import apiClient from '../services/apiClient';
import './AuthPage.css';

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'warning' | 'info'>('info');
  const [isLoading, setIsLoading] = useState(false);

  // Check for messages from navigation state (e.g., session expiration, registration success)
  useEffect(() => {
    if (location.state?.message) {
      setMessage(location.state.message);
      setMessageType(location.state.type || 'info');
      
      // Clear the message from location state
      window.history.replaceState({}, document.title);
      
      // Auto-clear message after 10 seconds
      const timer = setTimeout(() => {
        setMessage('');
      }, 10000);
      
      return () => clearTimeout(timer);
    }
  }, [location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setIsLoading(true);

    try {
      await apiClient.login(username, password);
      navigate('/chat');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <h1>Welcome Back</h1>
            <p className="text-muted">Sign in to continue to your workspace</p>
          </div>

          {message && (
            <div className={`alert alert-${messageType}`}>
              {message}
            </div>
          )}

          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="username" className="label">Username</label>
              <input
                id="username"
                type="text"
                className="input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                disabled={isLoading}
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="label">Password</label>
              <input
                id="password"
                type="password"
                className="input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                disabled={isLoading}
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary btn-full"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="auth-footer">
            <p className="text-muted">
              Don't have an account?{' '}
              <Link to="/register" className="link">Create one</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
