import React, { useState } from 'react';
import './Login.css';

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    
    // Simple hardcoded auth for demo (replace with real backend auth later)
    if (username === 'admin' && password === 'admin') {
      localStorage.setItem('user', JSON.stringify({ username, loginTime: new Date() }));
      onLoginSuccess(username);
    } else {
      setError('Invalid credentials. Try admin / admin');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1 className="login-title">🛡️ HALO</h1>
          <p className="login-subtitle">AI-Powered Construction Site Safety</p>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="form-input"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="login-btn">Login</button>
        </form>

        <p className="login-hint">Demo: admin / admin</p>
      </div>
    </div>
  );
}
