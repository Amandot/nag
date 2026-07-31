import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ComplaintHeatmap from '../components/ComplaintHeatmap';
import AnalyticsCharts from '../components/AnalyticsCharts';
import CriticalAlerts from '../components/CriticalAlerts';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'heatmap' | 'analytics' | 'alerts' | 'complaints' | 'reports'>('overview');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    navigate('/login');
  };

  const handleNavigateToComplaints = () => {
    navigate('/admin/complaints');
  };

  const handleNavigateToReports = () => {
    navigate('/admin/reports');
  };

  return (
    <div className="admin-dashboard">
      {/* Admin Navigation */}
      <nav className="admin-nav">
        <div className="admin-nav-brand">
          <h1>Admin Dashboard</h1>
        </div>
        <div className="admin-nav-tabs">
          <button
            className={activeTab === 'overview' ? 'active' : ''}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={activeTab === 'complaints' ? 'active' : ''}
            onClick={handleNavigateToComplaints}
          >
            Complaints
          </button>
          <button
            className={activeTab === 'heatmap' ? 'active' : ''}
            onClick={() => setActiveTab('heatmap')}
          >
            Heatmap
          </button>
          <button
            className={activeTab === 'analytics' ? 'active' : ''}
            onClick={() => setActiveTab('analytics')}
          >
            Analytics
          </button>
          <button
            className={activeTab === 'alerts' ? 'active' : ''}
            onClick={() => setActiveTab('alerts')}
          >
            Alerts
          </button>
          <button
            className={activeTab === 'reports' ? 'active' : ''}
            onClick={handleNavigateToReports}
          >
            Reports
          </button>
        </div>
        <div className="admin-nav-actions">
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </nav>

      {/* Dashboard Content */}
      <div className="admin-content">
        {activeTab === 'overview' && (
          <div className="overview-grid">
            <div className="overview-section alerts-section">
              <h2>Critical Alerts</h2>
              <CriticalAlerts limit={5} />
            </div>
            <div className="overview-section heatmap-section">
              <h2>Complaint Heatmap</h2>
              <ComplaintHeatmap height="400px" />
            </div>
            <div className="overview-section analytics-section">
              <h2>Quick Analytics</h2>
              <AnalyticsCharts compact={true} />
            </div>
          </div>
        )}

        {activeTab === 'heatmap' && (
          <div className="full-section">
            <h2>Complaint Heatmap</h2>
            <ComplaintHeatmap height="calc(100vh - 200px)" />
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="full-section">
            <h2>Analytics & Performance</h2>
            <AnalyticsCharts compact={false} />
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="full-section">
            <h2>Critical Alerts</h2>
            <CriticalAlerts limit={50} />
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
