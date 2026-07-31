import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { complaintsAPI, Complaint } from '../api/complaints';
import Navigation from '../components/Navigation';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);

  useEffect(() => {
    loadComplaints();
  }, []);

  const loadComplaints = async () => {
    const userId = localStorage.getItem('userId');
    if (!userId) {
      setError('User ID not found. Please log in again.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const data = await complaintsAPI.getUserComplaints(userId);
      console.log('Complaints loaded:', data);
      setComplaints(data);
    } catch (err: any) {
      console.error('Error loading complaints:', err);
      const errorMessage = err.response?.data?.error || err.response?.data?.message || err.message || 'Failed to load complaints';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (complaintId: string, e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation to complaint details
    
    if (!window.confirm('Are you sure you want to delete this complaint? This action cannot be undone.')) {
      return;
    }

    setDeleteLoading(complaintId);
    setError('');

    try {
      await complaintsAPI.delete(complaintId);
      // Remove from local state
      setComplaints(complaints.filter(c => c.complaint_id !== complaintId));
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to delete complaint');
    } finally {
      setDeleteLoading(null);
    }
  };

  const getPriorityClass = (priority: string) => {
    return `priority-badge priority-${priority.toLowerCase()}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div>
      <Navigation />
      <div className="container">
        <div className="dashboard-page">
          <div className="dashboard-header">
            <div>
              <h1>My Complaints</h1>
              <p className="dashboard-subtitle">Track and manage your submitted grievances</p>
            </div>
            <Link to="/submit" className="btn btn-primary">
              + New Complaint
            </Link>
          </div>

          {loading && (
            <div className="loading">Loading your complaints...</div>
          )}

          {error && (
            <div className="error">{error}</div>
          )}

          {!loading && !error && complaints.length === 0 && (
            <div className="empty-state">
              <h3>No complaints yet</h3>
              <p>Submit your first complaint to get started</p>
              <Link to="/submit" className="btn btn-primary">
                Submit Complaint
              </Link>
            </div>
          )}

          {!loading && !error && complaints.length > 0 && (
            <div className="complaints-grid">
              {complaints.map((complaint) => (
                <div key={complaint.complaint_id} className="complaint-card-wrapper">
                  <Link
                    to={`/complaint/${complaint.complaint_id}`}
                    className="complaint-card"
                  >
                    <div className="complaint-card-header">
                      <span className={getPriorityClass(complaint.priority_level)}>
                        {complaint.priority_level}
                      </span>
                      <span className="status-badge">{complaint.status}</span>
                    </div>

                    <div className="complaint-card-body">
                      <h3>{complaint.category}</h3>
                      <p className="complaint-card-description">
                        {complaint.description.length > 150
                          ? `${complaint.description.substring(0, 150)}...`
                          : complaint.description}
                      </p>
                    </div>

                    <div className="complaint-card-footer">
                      <span className="complaint-card-date">
                        {formatDate(complaint.created_at)}
                      </span>
                      <span className="complaint-card-score">
                        Score: {complaint.impact_score}/100
                      </span>
                    </div>
                  </Link>
                  <button
                    className="btn-delete"
                    onClick={(e) => handleDelete(complaint.complaint_id, e)}
                    disabled={deleteLoading === complaint.complaint_id}
                    title="Delete complaint"
                  >
                    {deleteLoading === complaint.complaint_id ? '⏳' : '🗑️'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
