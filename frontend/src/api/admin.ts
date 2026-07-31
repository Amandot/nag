import apiClient from './client';

export interface HeatmapLocation {
  location: {
    latitude: number;
    longitude: number;
    address: string;
  };
  complaint_count: number;
  avg_impact_score: number;
  priority_distribution: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
}

export interface HeatmapResponse {
  total_locations: number;
  heatmap_data: HeatmapLocation[];
  filters_applied: {
    status?: string;
    priority?: string;
    category?: string;
    days: number;
  };
}

export interface CategoryTrend {
  date: string;
  count: number;
}

export interface TrendsResponse {
  period: {
    start_date: string;
    end_date: string;
    days: number;
    interval: string;
  };
  trends: {
    [category: string]: CategoryTrend[];
  };
  totals: {
    [category: string]: number;
  };
}

export interface DepartmentMetrics {
  department: string;
  category: string;
  total_complaints: number;
  pending_complaints: number;
  resolved_complaints: number;
  avg_resolution_time_hours: number;
  total_officers: number;
  total_workload: number;
  avg_workload_per_officer: number;
  sla_violations: number;
  sla_compliance_rate: number;
}

export interface DepartmentPerformanceResponse {
  period_days: number;
  departments: DepartmentMetrics[];
}

export interface ResolutionTimeStats {
  count: number;
  avg_hours: number;
  min_hours: number;
  max_hours: number;
}

export interface ResolutionTimesResponse {
  period_days: number;
  overall: ResolutionTimeStats;
  by_category: {
    [category: string]: ResolutionTimeStats;
  };
  by_priority: {
    [priority: string]: ResolutionTimeStats;
  };
}

export interface Alert {
  alert_type: 'CRITICAL_PRIORITY' | 'ESCALATED' | 'APPROACHING_SLA';
  complaint: any;
  time_since_creation: string;
  reason: string;
  sla_deadline?: string;
  hours_remaining?: number;
}

export interface AlertsResponse {
  total_alerts: number;
  alerts: Alert[];
  summary: {
    critical_priority: number;
    escalated: number;
    approaching_sla: number;
  };
}

export const getHeatmapData = async (params?: {
  status?: string;
  priority?: string;
  category?: string;
  days?: number;
}): Promise<HeatmapResponse> => {
  const response = await apiClient.get('/admin/heatmap', { params });
  return response.data;
};

export const getCategoryTrends = async (params?: {
  days?: number;
  interval?: 'day' | 'week' | 'month';
}): Promise<TrendsResponse> => {
  const response = await apiClient.get('/admin/analytics/trends', { params });
  return response.data;
};

export const getDepartmentPerformance = async (params?: {
  days?: number;
}): Promise<DepartmentPerformanceResponse> => {
  const response = await apiClient.get('/admin/analytics/departments', { params });
  return response.data;
};

export const getResolutionTimes = async (params?: {
  days?: number;
}): Promise<ResolutionTimesResponse> => {
  const response = await apiClient.get('/admin/analytics/resolution-times', { params });
  return response.data;
};

export const getCriticalAlerts = async (params?: {
  limit?: number;
  include_high?: boolean;
}): Promise<AlertsResponse> => {
  const response = await apiClient.get('/admin/alerts', { params });
  return response.data;
};
