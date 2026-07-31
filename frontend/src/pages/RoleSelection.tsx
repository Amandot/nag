import React from 'react';
import { useNavigate } from 'react-router-dom';
import './RoleSelection.css';

const RoleSelection: React.FC = () => {
  const navigate = useNavigate();

  const handleRoleSelection = (role: 'user' | 'admin') => {
    navigate('/login', { state: { role } });
  };

  return (
    <div className="role-selection-container">
      <div className="role-selection-card">
        <div className="role-brand">
          <img src="/logo192.png" alt="NagrikSathi Logo" className="role-brand-logo" />
        </div>
        {/* <div className="role-brand">
          <img src="" alt="" className="role-brand-logo" />
          <span>NagrikSathi</span>
        </div> */}
        <div className="role-brand">
          <span className="role-brand-name">NagrikSathi</span>
        </div>
        <h1>Welcome to NagrikSathi</h1>
        <p className="subtitle">AI-Powered Citizen Grievance Portal - Please select your role to continue</p>
        
        <div className="role-options">
          <div className="role-card" onClick={() => handleRoleSelection('user')}>
            <div className="role-icon user-icon">👤</div>
            <h2>Citizen Login</h2>
            <p>Submit and track your complaints</p>
            <button className="role-btn user-btn">Login as Citizen</button>
          </div>

          <div className="role-card" onClick={() => handleRoleSelection('admin')}>
            <div className="role-icon admin-icon">👨‍💼</div>
            <h2>Admin Login</h2>
            <p>Manage and oversee all complaints</p>
            <button className="role-btn admin-btn">Login as Admin</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoleSelection;
