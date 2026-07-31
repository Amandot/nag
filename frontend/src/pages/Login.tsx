import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { authAPI } from '../api/auth';
import './Auth.css';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const expectedRole = (location.state as any)?.role || 'user';
  
  const [formData, setFormData] = useState({
    credential: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.credential || !formData.password) {
      setError('All fields are required');
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.login({
        credential: formData.credential,
        password: formData.password,
      });

      // Store token, user ID, and role
      localStorage.setItem('token', response.token);
      localStorage.setItem('userId', response.user_id);
      localStorage.setItem('userRole', response.role);
      localStorage.setItem('userName', response.name);

      // Check if user role matches expected role
      if (expectedRole === 'admin' && response.role !== 'admin') {
        setError('Access denied. This account does not have admin privileges.');
        localStorage.clear();
        return;
      }

      // Navigate based on role
      if (response.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-brand">
          <img src="/logo192.png" alt="NagrikSathi Logo" className="auth-brand-logo" />
          <span>NagrikSathi</span>
        </div>
        <div className="role-badge">
          {expectedRole === 'admin' ? '👨‍💼 Admin Login' : '👤 Citizen Login'}
        </div>
        <h1>Login</h1>
        <p className="auth-subtitle">
          {expectedRole === 'admin' 
            ? 'Access admin dashboard' 
            : 'Access your grievance dashboard'}
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="credential">Email or Phone</label>
            <input
              type="text"
              id="credential"
              name="credential"
              value={formData.credential}
              onChange={handleChange}
              placeholder="Enter your email or phone"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              disabled={loading}
            />
          </div>

          {error && <div className="error">{error}</div>}

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="auth-link">
          <Link to="/">← Back to role selection</Link>
        </p>
        <p className="auth-link">
          Don't have an account? <Link to="/register">Register here</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
