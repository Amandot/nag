/**
 * Admin Complaints API Client
 * 
 * Provides API methods for admin complaint management including:
 * - Fetching all complaints with filters
 * - Viewing complaint timelines
 * - Updating complaint status
 * - Adding notes
 * - Generating reports
 */

import apiClient from './client';

export interface ComplaintFilters {
  status?: string;
  category?: string;
  priority?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface TimelineEntry {
  history_id: string;
  old_status: string | null;
  new_status: string;
  changed_at: string;
  changed_by: {
    user_id: string;
    name: string;
    role: string;
  } | null;
  notes: string;
  time_in_previous_status: {
    seconds: number;
    hours: number;
    days: number;
    formatted: string;
  } | null;
}

export interface TimelineResponse {
  complaint_id: string;
  complaint: any;
  timeline: TimelineEntry[];
  time_in_current_status: {
    seconds: number;
    hours: number;
    days: number;
    formatted: string;
  } | null;
  time_in_each_status: {
    [status: string]: {
      seconds: number;
      hours: number;
      days: number;
      formatted: string;
    };
  };
  overall_resolution_time: {
    seconds: number;
    hours: number;
    days: number;
    formatted: string;
  } | null;
  total_status_changes: number;
}

export interface DashboardSummary {
  summary: {
    active_complaints: number;
    pending_complaints: number;
    resolved_complaints: number;
    escalated_complaints: number;
    total_complaints: number;
  };
  by_priority: {
    [key: string]: number;
  };
  by_category: {
    [key: string]: number;
  };
  by_status: {
    [key: string]: number;
  };
  recent_activity: {
    submissions_last_24h: number;
    resolutions_last_24h: number;
    avg_resolution_time_hours: number;
  };
}

export interface ReportFilters {
  start_date?: string;
  end_date?: string;
  format?: 'json' | 'csv';
  category?: string;
  priority?: string;
}

/**
 * Fetch all complaints with filtering and pagination
 */
export const getAllComplaints = async (filters: ComplaintFilters = {}) => {
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, value.toString());
    }
  });
  
  const response = await apiClient.get(`/admin/complaints?${params.toString()}`);
  return response.data;
};

/**
 * Get detailed timeline for a specific complaint
 */
export const getComplaintTimeline = async (complaintId: string): Promise<TimelineResponse> => {
  const response = await apiClient.get(`/admin/complaints/${complaintId}/timeline`);
  return response.data;
};

/**
 * Update complaint status (admin only)
 */
export const updateComplaintStatus = async (
  complaintId: string,
  status: string,
  notes?: string,
  assignedOfficerId?: string
) => {
  const response = await apiClient.put(`/admin/complaints/${complaintId}/status`, {
    status,
    notes,
    assigned_officer_id: assignedOfficerId,
  });
  return response.data;
};

/**
 * Add a note to a complaint without changing status
 */
export const addComplaintNote = async (complaintId: string, notes: string) => {
  const response = await apiClient.post(`/admin/complaints/${complaintId}/notes`, {
    notes,
  });
  return response.data;
};

/**
 * Get dashboard summary statistics
 */
export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const response = await apiClient.get('/admin/dashboard/summary');
  return response.data;
};

/**
 * Generate resolution time report
 */
export const generateResolutionReport = async (filters: ReportFilters = {}) => {
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, value.toString());
    }
  });
  
  if (filters.format === 'csv') {
    // For CSV, we need to handle the response differently
    const response = await apiClient.get(`/admin/reports/resolution-times?${params.toString()}`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'resolution_report.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return { message: 'Report downloaded' };
  }
  
  const response = await apiClient.get(`/admin/reports/resolution-times?${params.toString()}`);
  return response.data;
};
