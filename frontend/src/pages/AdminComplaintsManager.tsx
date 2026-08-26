import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getAllComplaints,
  getDashboardSummary,
  ComplaintFilters,
  DashboardSummary,
} from '../api/adminComplaints';
import './AdminComplaintsManager.css';

interface Complaint {
  complaint_id: string;
  description: string;
  category: string;
  status: string;
  priority_level: string;
  impact_score: number;
  created_at: string;
  location?: {
    latitude: number;
    longitude: number;
    address: string;
  } | null;
  user: {
    name: string;
    email: string;
    phone: string;
  };
  assigned_officer?: {
    name: string;
    department: string;
  };
  latest_update?: {
    changed_at: string;
    notes: string;
  };
  media_urls?: string[];
}

const AdminComplaintsManager: React.FC = () => {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [filters, setFilters] = useState<ComplaintFilters>({
    page: 1,
    per_page: 20,
    sort_by: 'created_at',
    sort_order: 'desc',
  });
  
  // Pagination
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total_items: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false,
  });

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load complaints and summary in parallel
      const [complaintsData, summaryData] = await Promise.all([
        getAllComplaints(filters),
        getDashboardSummary(),
      ]);
      
      setComplaints(complaintsData.complaints);
      setPagination(complaintsData.pagination);
      setSummary(summaryData);
    } catch (err: any) {
      console.error('Error loading data:', err);
      setError(err.response?.data?.error || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: 1, // Reset to first page when filters change
    }));
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({
      ...prev,
      page: newPage,
    }));
  };

  const handleViewTimeline = (complaintId: string) => {
    navigate(`/admin/complaints/${complaintId}/timeline`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Submitted':
        return 'status-submitted';
      case 'Assigned':
        return 'status-assigned';
      case 'In Progress':
        return 'status-in-progress';
      case 'Resolved':
        return 'status-resolved';
      case 'Escalated':
        return 'status-escalated';
      default:
        return '';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'Critical':
        return 'priority-critical';
      case 'High':
        return 'priority-high';
      case 'Medium':
        return 'priority-medium';
      case 'Low':
        return 'priority-low';
      default:
        return '';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading && !summary) {
    return (
      <div className="admin-complaints-manager">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="admin-complaints-manager">
      {/* Dashboard Summary */}
      {summary && (
        <div className="dashboard-summary">
          <div className="summary-card">
            <h3>Active</h3>
            <div className="summary-value">{summary.summary.active_complaints}</div>
          </div>
          <div className="summary-card">
            <h3>Pending</h3>
            <div className="summary-value">{summary.summary.pending_complaints}</div>
          </div>
          <div className="summary-card">
            <h3>Resolved</h3>
            <div className="summary-value">{summary.summary.resolved_complaints}</div>
          </div>
          <div className="summary-card escalated">
            <h3>Escalated</h3>
            <div className="summary-value">{summary.summary.escalated_complaints}</div>
          </div>
          <div className="summary-card">
            <h3>Total</h3>
            <div className="summary-value">{summary.summary.total_complaints}</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <h2>Filter Complaints</h2>
        <div className="filters-grid">
          <div className="filter-group">
            <label>Status</label>
            <select
              value={filters.status || ''}
              onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
            >
              <option value="">All Statuses</option>
              <option value="Submitted">Submitted</option>
              <option value="Assigned">Assigned</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
              <option value="Escalated">Escalated</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Priority</label>
            <select
              value={filters.priority || ''}
              onChange={(e) => handleFilterChange('priority', e.target.value || undefined)}
            >
              <option value="">All Priorities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Category</label>
            <select
              value={filters.category || ''}
              onChange={(e) => handleFilterChange('category', e.target.value || undefined)}
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
            <label>Search</label>
            <input
              type="text"
              placeholder="Search by ID or description..."
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value || undefined)}
            />
          </div>

          <div className="filter-group">
            <label>Sort By</label>
            <select
              value={filters.sort_by || 'created_at'}
              onChange={(e) => handleFilterChange('sort_by', e.target.value)}
            >
              <option value="created_at">Date Created</option>
              <option value="priority_level">Priority</option>
              <option value="status">Status</option>
              <option value="impact_score">Impact Score</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Order</label>
            <select
              value={filters.sort_order || 'desc'}
              onChange={(e) => handleFilterChange('sort_order', e.target.value as 'asc' | 'desc')}
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>

        <button className="clear-filters-btn" onClick={() => setFilters({ page: 1, per_page: 20 })}>
          Clear Filters
        </button>
      </div>

      {/* Error Display */}
      {error && <div className="error-message">{error}</div>}

      {/* Complaints Table */}
      <div className="complaints-section">
        <div className="section-header">
          <h2>Complaints ({pagination.total_items})</h2>
          <button className="refresh-btn" onClick={loadData} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {loading ? (
          <div className="loading">Loading complaints...</div>
        ) : complaints.length === 0 ? (
          <div className="no-data">No complaints found</div>
        ) : (
          <>
            <div className="complaints-table">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Location</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {complaints.map((complaint) => (
                    <tr key={complaint.complaint_id}>
                      <td className="complaint-id">
                        {complaint.complaint_id.substring(0, 8)}...
                      </td>
                      <td>
                        <div className="user-info">
                          <div className="user-name">{complaint.user.name}</div>
                          <div className="user-contact">{complaint.user.email}</div>
                        </div>
                      </td>
                      <td>{complaint.category}</td>
                      <td className="description">
                        {complaint.description.substring(0, 100)}
                        {complaint.description.length > 100 && '...'}
                      </td>
                      <td className="location-cell">
                        {complaint.location?.address ? (
                          <span title={`${complaint.location.address} (${complaint.location.latitude.toFixed(4)}, ${complaint.location.longitude.toFixed(4)})`}>
                            {complaint.location.address.length > 40
                              ? complaint.location.address.substring(0, 40) + '...'
                              : complaint.location.address}
                          </span>
                        ) : (
                          <span className="no-location">— No location</span>
                        )}
                      </td>
                      <td>
                        <span className={`priority-badge ${getPriorityColor(complaint.priority_level)}`}>
                          {complaint.priority_level}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${getStatusColor(complaint.status)}`}>
                          {complaint.status}
                        </span>
                      </td>
                      <td>{formatDate(complaint.created_at)}</td>
                      <td>
                        <button
                          className="view-timeline-btn"
                          onClick={() => handleViewTimeline(complaint.complaint_id)}
                        >
                          View Timeline
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="pagination">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={!pagination.has_prev}
              >
                Previous
              </button>
              <span className="page-info">
                Page {pagination.page} of {pagination.total_pages}
              </span>
              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={!pagination.has_next}
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AdminComplaintsManager;
