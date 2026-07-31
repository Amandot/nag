import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCriticalAlerts, AlertsResponse } from '../api/admin';
import './CriticalAlerts.css';

interface CriticalAlertsProps {
  limit?: number;
}

const CriticalAlerts: React.FC<CriticalAlertsProps> = ({ limit = 50 }) => {
  const navigate = useNavigate();
  const [alertsData, setAlertsData] = useState<AlertsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [includeHigh, setIncludeHigh] = useState(false);

  useEffect(() => {
    fetchAlerts();

    // Set up auto-refresh every 30 seconds if enabled
    let intervalId: NodeJS.Timeout | null = null;
    if (autoRefresh) {
      intervalId = setInterval(() => {
        fetchAlerts();
      }, 30000); // 30 seconds
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [limit, includeHigh, autoRefresh]);

  const fetchAlerts = async () => {
    try {
      setError(null);
      const response = await getCriticalAlerts({ limit, include_high: includeHigh });
      setAlertsData(response);
    } catch (err: any) {
      console.error('Error fetching critical alerts:', err);
      setError(err.response?.data?.error || 'Failed to load critical alerts');
    } finally {
      setLoading(false);
    }
  };

  const getAlertTypeLabel = (type: string): string => {
    switch (type) {
      case 'CRITICAL_PRIORITY':
        return 'Critical Priority';
      case 'ESCALATED':
        return 'Escalated';
      case 'APPROACHING_SLA':
        return 'SLA Warning';
      default:
        return type;
    }
  };

  const getAlertTypeClass = (type: string): string => {
    switch (type) {
      case 'CRITICAL_PRIORITY':
        return 'alert-critical';
      case 'ESCALATED':
        return 'alert-escalated';
      case 'APPROACHING_SLA':
        return 'alert-warning';
      default:
        return '';
    }
  };

  const getPriorityClass = (priority: string): string => {
    switch (priority?.toLowerCase()) {
      case 'critical':
        return 'priority-critical';
      case 'high':
        return 'priority-high';
      case 'medium':
        return 'priority-medium';
      case 'low':
        return 'priority-low';
      default:
        return '';
    }
  };

  const formatTimeSince = (timeString: string): string => {
    // Parse the time string (format: "X days, HH:MM:SS" or "HH:MM:SS")
    const parts = timeString.split(',');
    if (parts.length > 1) {
      return parts[0].trim(); // Return just the days part
    }
    
    const timeParts = timeString.split(':');
    if (timeParts.length === 3) {
      const hours = parseInt(timeParts[0]);
      if (hours > 24) {
        const days = Math.floor(hours / 24);
        return `${days} day${days > 1 ? 's' : ''}`;
      }
      return `${hours} hour${hours !== 1 ? 's' : ''}`;
    }
    
    return timeString;
  };

  const handleAlertClick = (complaintId: string) => {
    navigate(`/complaint/${complaintId}`);
  };

  if (loading) {
    return (
      <div className="alerts-loading">
        <p>Loading alerts...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alerts-error">
        <p>Error: {error}</p>
        <button onClick={fetchAlerts}>Retry</button>
      </div>
    );
  }

  return (
    <div className="critical-alerts">
      {/* Controls */}
      <div className="alerts-controls">
        <div className="alerts-summary">
          <span className="summary-item critical">
            <strong>{alertsData?.summary.critical_priority || 0}</strong> Critical
          </span>
          <span className="summary-item escalated">
            <strong>{alertsData?.summary.escalated || 0}</strong> Escalated
          </span>
          <span className="summary-item warning">
            <strong>{alertsData?.summary.approaching_sla || 0}</strong> SLA Warning
          </span>
        </div>

        <div className="alerts-options">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includeHigh}
              onChange={(e) => setIncludeHigh(e.target.checked)}
            />
            Include High Priority
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh (30s)
          </label>

          <button onClick={fetchAlerts} className="refresh-btn">
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Alerts List */}
      <div className="alerts-list">
        {alertsData?.alerts && alertsData.alerts.length > 0 ? (
          alertsData.alerts.map((alert, index) => (
            <div
              key={index}
              className={`alert-card ${getAlertTypeClass(alert.alert_type)}`}
              onClick={() => handleAlertClick(alert.complaint.complaint_id)}
            >
              <div className="alert-header">
                <span className="alert-type-badge">
                  {getAlertTypeLabel(alert.alert_type)}
                </span>
                <span className={`priority-badge ${getPriorityClass(alert.complaint.priority_level)}`}>
                  {alert.complaint.priority_level}
                </span>
              </div>

              <div className="alert-body">
                <div className="alert-id">
                  <strong>ID:</strong> {alert.complaint.complaint_id.substring(0, 8)}...
                </div>
                <div className="alert-category">
                  <strong>Category:</strong> {alert.complaint.category}
                </div>
                <div className="alert-location">
                  <strong>Location:</strong> {alert.complaint.location?.address || 'N/A'}
                </div>
                <div className="alert-reason">
                  {alert.reason}
                </div>
              </div>

              <div className="alert-footer">
                <span className="alert-time">
                  Created: {formatTimeSince(alert.time_since_creation)} ago
                </span>
                {alert.hours_remaining !== undefined && (
                  <span className="alert-sla">
                    {alert.hours_remaining.toFixed(1)}h remaining
                  </span>
                )}
                <span className="alert-score">
                  Impact: {alert.complaint.impact_score}
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="no-alerts">
            <p>✓ No critical alerts at this time</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CriticalAlerts;
