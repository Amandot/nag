import React, { useState } from 'react';
import { generateResolutionReport, ReportFilters } from '../api/adminComplaints';
import './AdminReports.css';

interface ReportData {
  complaint_id: string;
  category: string;
  priority: string;
  created_at: string;
  resolved_at: string;
  resolution_time_hours: number;
  time_in_submitted: number;
  time_in_assigned: number;
  time_in_progress: number;
  time_in_escalated: number;
  total_status_changes: number;
}

const AdminReports: React.FC = () => {
  const [filters, setFilters] = useState<ReportFilters>({});
  const [reportData, setReportData] = useState<ReportData[] | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateReport = async (format: 'json' | 'csv' = 'json') => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await generateResolutionReport({ ...filters, format });
      
      if (format === 'json') {
        setReportData(data.report);
        setSummary(data.summary);
      }
    } catch (err: any) {
      console.error('Error generating report:', err);
      setError(err.response?.data?.error || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
    }));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatHours = (hours: number) => {
    if (hours >= 24) {
      return `${(hours / 24).toFixed(1)} days`;
    }
    return `${hours.toFixed(1)} hours`;
  };

  return (
    <div className="admin-reports">
      <h1>Resolution Time Reports</h1>

      {/* Filters */}
      <div className="report-filters">
        <h2>Report Filters</h2>
        <div className="filters-grid">
          <div className="filter-group">
            <label>Start Date</label>
            <input
              type="date"
              value={filters.start_date || ''}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label>End Date</label>
            <input
              type="date"
              value={filters.end_date || ''}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label>Category</label>
            <select
              value={filters.category || ''}
              onChange={(e) => handleFilterChange('category', e.target.value)}
            >
              <option value="">All Categories</option>
              <option value="Water Supply">Water Supply</option>
              <option value="Electricity">Electricity</option>
              <option value="Roads & Infrastructure">Roads & Infrastructure</option>
              <option value="Healthcare">Healthcare</option>
              <option value="Public Safety">Public Safety</option>
              <option value="Sanitation">Sanitation</option>
              <option value="Other">Other</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Priority</label>
            <select
              value={filters.priority || ''}
              onChange={(e) => handleFilterChange('priority', e.target.value)}
            >
              <option value="">All Priorities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </div>

        <div className="report-actions">
          <button
            className="generate-btn"
            onClick={() => handleGenerateReport('json')}
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
          <button
            className="export-btn"
            onClick={() => handleGenerateReport('csv')}
            disabled={loading}
          >
            Export as CSV
          </button>
          <button
            className="clear-btn"
            onClick={() => {
              setFilters({});
              setReportData(null);
              setSummary(null);
            }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && <div className="error-message">{error}</div>}

      {/* Summary */}
      {summary && (
        <div className="report-summary">
          <h2>Summary</h2>
          <div className="summary-cards">
            <div className="summary-card">
              <h3>Total Complaints</h3>
              <div className="summary-value">{summary.total_complaints}</div>
            </div>
            <div className="summary-card">
              <h3>Average Resolution Time</h3>
              <div className="summary-value">
                {formatHours(summary.avg_resolution_time_hours)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Report Data */}
      {reportData && reportData.length > 0 && (
        <div className="report-data">
          <h2>Detailed Report ({reportData.length} complaints)</h2>
          <div className="report-table-container">
            <table className="report-table">
              <thead>
                <tr>
                  <th>Complaint ID</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Created</th>
                  <th>Resolved</th>
                  <th>Total Time</th>
                  <th>Submitted</th>
                  <th>Assigned</th>
                  <th>In Progress</th>
                  <th>Escalated</th>
                  <th>Status Changes</th>
                </tr>
              </thead>
              <tbody>
                {reportData.map((row) => (
                  <tr key={row.complaint_id}>
                    <td className="complaint-id">
                      {row.complaint_id.substring(0, 8)}...
                    </td>
                    <td>{row.category}</td>
                    <td>
                      <span className={`priority-badge priority-${row.priority.toLowerCase()}`}>
                        {row.priority}
                      </span>
                    </td>
                    <td>{formatDate(row.created_at)}</td>
                    <td>{formatDate(row.resolved_at)}</td>
                    <td className="time-cell">
                      {formatHours(row.resolution_time_hours)}
                    </td>
                    <td className="time-cell">
                      {row.time_in_submitted > 0 ? formatHours(row.time_in_submitted) : '-'}
                    </td>
                    <td className="time-cell">
                      {row.time_in_assigned > 0 ? formatHours(row.time_in_assigned) : '-'}
                    </td>
                    <td className="time-cell">
                      {row.time_in_progress > 0 ? formatHours(row.time_in_progress) : '-'}
                    </td>
                    <td className="time-cell">
                      {row.time_in_escalated > 0 ? formatHours(row.time_in_escalated) : '-'}
                    </td>
                    <td>{row.total_status_changes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {reportData && reportData.length === 0 && (
        <div className="no-data">No resolved complaints found for the selected filters</div>
      )}
    </div>
  );
};

export default AdminReports;
