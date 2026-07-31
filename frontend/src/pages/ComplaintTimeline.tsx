import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getComplaintTimeline,
  updateComplaintStatus,
  addComplaintNote,
  TimelineResponse,
} from '../api/adminComplaints';
import './ComplaintTimeline.css';

const ComplaintTimeline: React.FC = () => {
  const { complaintId } = useParams<{ complaintId: string }>();
  const navigate = useNavigate();
  
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Status update form
  const [showStatusForm, setShowStatusForm] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [statusNotes, setStatusNotes] = useState('');
  const [updating, setUpdating] = useState(false);
  
  // Note form
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [addingNote, setAddingNote] = useState(false);

  useEffect(() => {
    if (complaintId) {
      loadTimeline();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [complaintId]);

  const loadTimeline = async () => {
    if (!complaintId) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await getComplaintTimeline(complaintId);
      setTimeline(data);
    } catch (err: any) {
      console.error('Error loading timeline:', err);
      setError(err.response?.data?.error || 'Failed to load timeline');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaintId || !newStatus) return;
    
    try {
      setUpdating(true);
      await updateComplaintStatus(complaintId, newStatus, statusNotes);
      
      // Reload timeline
      await loadTimeline();
      
      // Reset form
      setShowStatusForm(false);
      setNewStatus('');
      setStatusNotes('');
    } catch (err: any) {
      console.error('Error updating status:', err);
      alert(err.response?.data?.error || 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaintId || !noteText.trim()) return;
    
    try {
      setAddingNote(true);
      await addComplaintNote(complaintId, noteText);
      
      // Reload timeline
      await loadTimeline();
      
      // Reset form
      setShowNoteForm(false);
      setNoteText('');
    } catch (err: any) {
      console.error('Error adding note:', err);
      alert(err.response?.data?.error || 'Failed to add note');
    } finally {
      setAddingNote(false);
    }
  };

  const formatDuration = (duration: { hours: number; days: number; formatted: string }) => {
    if (duration.days >= 1) {
      return `${duration.days.toFixed(1)} days`;
    } else if (duration.hours >= 1) {
      return `${duration.hours.toFixed(1)} hours`;
    } else {
      return duration.formatted;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Submitted':
        return '📝';
      case 'Assigned':
        return '👤';
      case 'In Progress':
        return '⚙️';
      case 'Resolved':
        return '✅';
      case 'Escalated':
        return '⚠️';
      default:
        return '•';
    }
  };

  if (loading) {
    return (
      <div className="complaint-timeline">
        <div className="loading">Loading timeline...</div>
      </div>
    );
  }

  if (error || !timeline) {
    return (
      <div className="complaint-timeline">
        <div className="error-message">{error || 'Timeline not found'}</div>
        <button onClick={() => navigate('/admin/complaints')}>Back to Complaints</button>
      </div>
    );
  }

  const complaint = timeline.complaint;

  return (
    <div className="complaint-timeline">
      {/* Header */}
      <div className="timeline-header">
        <button className="back-btn" onClick={() => navigate('/admin/complaints')}>
          ← Back to Complaints
        </button>
        <h1>Complaint Timeline</h1>
      </div>

      {/* Complaint Details */}
      <div className="complaint-details-card">
        <div className="detail-row">
          <span className="label">ID:</span>
          <span className="value">{complaint.complaint_id}</span>
        </div>
        <div className="detail-row">
          <span className="label">Category:</span>
          <span className="value">{complaint.category}</span>
        </div>
        <div className="detail-row">
          <span className="label">Priority:</span>
          <span className={`value priority-${complaint.priority_level.toLowerCase()}`}>
            {complaint.priority_level}
          </span>
        </div>
        <div className="detail-row">
          <span className="label">Current Status:</span>
          <span className={`value status-${complaint.status.toLowerCase().replace(' ', '-')}`}>
            {complaint.status}
          </span>
        </div>
        <div className="detail-row">
          <span className="label">Description:</span>
          <span className="value">{complaint.description}</span>
        </div>
      </div>

      {/* Time Analysis */}
      <div className="time-analysis">
        <h2>Time Analysis</h2>
        <div className="time-cards">
          {timeline.overall_resolution_time && (
            <div className="time-card overall">
              <h3>Total Resolution Time</h3>
              <div className="time-value">
                {formatDuration(timeline.overall_resolution_time)}
              </div>
            </div>
          )}
          
          {timeline.time_in_current_status && (
            <div className="time-card current">
              <h3>Time in Current Status</h3>
              <div className="time-value">
                {formatDuration(timeline.time_in_current_status)}
              </div>
            </div>
          )}
          
          {Object.entries(timeline.time_in_each_status).map(([status, duration]) => (
            <div key={status} className="time-card">
              <h3>{status}</h3>
              <div className="time-value">{formatDuration(duration)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button
          className="update-status-btn"
          onClick={() => setShowStatusForm(!showStatusForm)}
        >
          Update Status
        </button>
        <button
          className="add-note-btn"
          onClick={() => setShowNoteForm(!showNoteForm)}
        >
          Add Note
        </button>
      </div>

      {/* Status Update Form */}
      {showStatusForm && (
        <div className="status-form-card">
          <h3>Update Status</h3>
          <form onSubmit={handleUpdateStatus}>
            <div className="form-group">
              <label>New Status</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                required
              >
                <option value="">Select Status</option>
                <option value="Submitted">Submitted</option>
                <option value="Assigned">Assigned</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
                <option value="Escalated">Escalated</option>
              </select>
            </div>
            <div className="form-group">
              <label>Notes (optional)</label>
              <textarea
                value={statusNotes}
                onChange={(e) => setStatusNotes(e.target.value)}
                placeholder="Add notes about this status change..."
                rows={3}
              />
            </div>
            <div className="form-actions">
              <button type="submit" disabled={updating}>
                {updating ? 'Updating...' : 'Update Status'}
              </button>
              <button type="button" onClick={() => setShowStatusForm(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Note Form */}
      {showNoteForm && (
        <div className="note-form-card">
          <h3>Add Note</h3>
          <form onSubmit={handleAddNote}>
            <div className="form-group">
              <label>Note</label>
              <textarea
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Add a progress update or note..."
                rows={4}
                required
              />
            </div>
            <div className="form-actions">
              <button type="submit" disabled={addingNote}>
                {addingNote ? 'Adding...' : 'Add Note'}
              </button>
              <button type="button" onClick={() => setShowNoteForm(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Timeline */}
      <div className="timeline-section">
        <h2>Status History ({timeline.total_status_changes} changes)</h2>
        <div className="timeline-container">
          {timeline.timeline.map((entry, index) => (
            <div key={entry.history_id} className="timeline-entry">
              <div className="timeline-marker">
                <div className="timeline-icon">{getStatusIcon(entry.new_status)}</div>
                {index < timeline.timeline.length - 1 && <div className="timeline-line" />}
              </div>
              <div className="timeline-content">
                <div className="timeline-status">
                  {entry.old_status && (
                    <span className="old-status">{entry.old_status}</span>
                  )}
                  {entry.old_status && <span className="arrow">→</span>}
                  <span className="new-status">{entry.new_status}</span>
                </div>
                <div className="timeline-meta">
                  <span className="timeline-date">
                    {new Date(entry.changed_at).toLocaleString()}
                  </span>
                  {entry.changed_by && (
                    <span className="timeline-user">
                      by {entry.changed_by.name} ({entry.changed_by.role})
                    </span>
                  )}
                </div>
                {entry.time_in_previous_status && (
                  <div className="timeline-duration">
                    Time in previous status: {formatDuration(entry.time_in_previous_status)}
                  </div>
                )}
                {entry.notes && (
                  <div className="timeline-notes">
                    <strong>Notes:</strong> {entry.notes}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ComplaintTimeline;
