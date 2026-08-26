import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { complaintsAPI, Complaint, StatusHistory } from '../api/complaints';
import Navigation from '../components/Navigation';
import FeedbackForm from '../components/FeedbackForm';
import './ComplaintDetails.css';

const ComplaintDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [history, setHistory] = useState<StatusHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showFeedback, setShowFeedback] = useState(false);

  useEffect(() => {
    loadComplaintData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadComplaintData = async () => {
    if (!id) return;

    setLoading(true);
    setError('');

    try {
      const [complaintData, historyData] = await Promise.all([
        complaintsAPI.getById(id),
        complaintsAPI.getHistory(id),
      ]);

      setComplaint(complaintData);
      setHistory(historyData);

      // Show feedback form if complaint is resolved
      if (complaintData.status === 'Resolved') {
        setShowFeedback(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load complaint details');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityClass = (priority: string) => {
    return `priority-badge priority-${priority.toLowerCase()}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div>
        <Navigation />
        <div className="container">
          <div className="loading">Loading complaint details...</div>
        </div>
      </div>
    );
  }

  if (error || !complaint) {
    return (
      <div>
        <Navigation />
        <div className="container">
          <div className="error">{error || 'Complaint not found'}</div>
          <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Navigation />
      <div className="container">
        <div className="complaint-details-page">
          <div className="page-header">
            <div>
              <h1>Complaint Details</h1>
              <p className="complaint-id">ID: {complaint.complaint_id}</p>
            </div>
            <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
              Back to Dashboard
            </button>
          </div>

          <div className="card">
            <div className="complaint-header">
              <div>
                <span className={getPriorityClass(complaint.priority_level)}>
                  {complaint.priority_level}
                </span>
                <span className="status-badge">{complaint.status}</span>
              </div>
              <div className="complaint-meta">
                <p>Category: <strong>{complaint.category}</strong></p>
                <p>Impact Score: <strong>{complaint.impact_score}/100</strong></p>
              </div>
            </div>

            {complaint.image_analysis && (
              <div className="complaint-section">
                <h3>Image Analysis (CNN)</h3>
                <div className="ml-results-box">
                  <p><strong>Predicted Category:</strong> {complaint.image_analysis.category}</p>
                  <p><strong>Detected Issue:</strong> {complaint.image_analysis.issue}</p>
                  <p><strong>Image Severity:</strong> {complaint.image_analysis.severity}</p>
                  <p><strong>Image Score:</strong> {complaint.image_analysis.severity_score} / 100</p>
                  <p><strong>Model Confidence:</strong> {(complaint.image_analysis.confidence * 100).toFixed(1)}%</p>
                </div>
              </div>
            )}

            <div className="complaint-section">
              <h3>Description</h3>
              <p className="complaint-description">{complaint.description}</p>
            </div>

            <div className="complaint-section">
              <h3>Location</h3>
              {complaint.location ? (
                <>
                  <p>{complaint.location.address || 'Address not available'}</p>
                  <p className="location-coords">
                    Coordinates: {complaint.location.latitude?.toFixed(6) || 'N/A'}, {complaint.location.longitude?.toFixed(6) || 'N/A'}
                  </p>
                </>
              ) : (
                <p>Location information not available</p>
              )}
            </div>

            <div className="complaint-section">
              <h3>Priority Explanation</h3>
              <div className="explanation-box">
                <p>{complaint.explanation}</p>
              </div>
            </div>

            <div className="complaint-section">
              <h3>Status timeline</h3>
              <p className="timeline-description">When the admin updates your complaint status, it appears here with time and any notes.</p>
              <div className="timeline">
                {history.length === 0 ? (
                  <div className="timeline-item">
                    <div className="timeline-marker"></div>
                    <div className="timeline-content">
                      <p className="timeline-status">Submitted</p>
                      <p className="timeline-date">{formatDate(complaint.created_at)}</p>
                    </div>
                  </div>
                ) : (
                  history.map((item, index) => (
                    <div key={item.history_id || index} className="timeline-item">
                      <div className="timeline-marker"></div>
                      <div className="timeline-content">
                        <p className="timeline-status">{item.new_status}</p>
                        <p className="timeline-date">{formatDate(item.changed_at)}</p>
                        {item.notes && (
                          <p className="timeline-notes">{item.notes}</p>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {showFeedback && (
            <div className="card">
              <h3>Provide Feedback</h3>
              <p className="feedback-subtitle">
                Help us improve by rating your experience with this complaint resolution
              </p>
              <FeedbackForm complaintId={complaint.complaint_id} onSuccess={() => setShowFeedback(false)} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ComplaintDetails;
