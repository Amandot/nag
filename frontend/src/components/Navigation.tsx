import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../api/auth';
import './Navigation.css';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const userName = localStorage.getItem('userName') || 'User';
  const userRole = localStorage.getItem('userRole') || 'citizen';

  const handleLogout = () => {
    authAPI.logout();
    navigate('/login');
  };

  const isActive = (path: string) => {
    return location.pathname === path ? 'active' : '';
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  return (
    <nav className="navigation">
      <div className="nav-container">
        <Link to="/dashboard" className="nav-brand">
          <img src="/logo192.png" alt="NagrikSathi" className="nav-brand-logo" />
          <div className="nav-brand-text">
            <span className="nav-brand-title">NagrikSathi</span>
            <span className="nav-brand-subtitle">Citizen Grievance Portal</span>
          </div>
        </Link>
        
        <button className="nav-toggle" onClick={toggleMobileMenu}>
          {mobileMenuOpen ? '✕' : '☰'}
        </button>
        
        <div className={`nav-menu ${mobileMenuOpen ? 'active' : ''}`}>
          <div className="nav-links">
            <Link 
              to="/dashboard" 
              className={`nav-link ${isActive('/dashboard')}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              📊 Dashboard
            </Link>
            <Link 
              to="/submit" 
              className={`nav-link ${isActive('/submit')}`}
              onClick={() => setMobileMenuOpen(false)}
            >
              ✍️ Submit Complaint
            </Link>
          </div>
          
          <div className="nav-user">
            <div className="nav-user-info">
              <span className="nav-user-name">{userName}</span>
              <span className="nav-user-role">{userRole}</span>
            </div>
            <button onClick={handleLogout} className="nav-logout">
              🚪 Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
