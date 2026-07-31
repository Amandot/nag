import apiClient from './client';

/** Complaint categories available for user selection */
export const COMPLAINT_CATEGORIES = [
  'Water Supply',
  'Electricity',
  'Roads & Infrastructure',
  'Healthcare',
  'Public Safety',
  'Sanitation',
  'Other',
] as const;

export type ComplaintCategory = typeof COMPLAINT_CATEGORIES[number];

export interface ComplaintSubmission {
  description: string;
  category: string;
  location: {
    latitude: number;
    longitude: number;
    address: string;
  };
  media_urls?: string[];
}

export interface Complaint {
  complaint_id: string;
  user_id: string;
  category: string;
  description: string;
  location: {
    latitude: number;
    longitude: number;
    address: string;
  } | null;
  priority_level: string;
  impact_score: number;
  status: string;
  explanation: string;
  created_at: string;
  assigned_at?: string;
  resolved_at?: string;
}

export interface StatusHistory {
  history_id: string;
  complaint_id: string;
  old_status: string | null;
  new_status: string;
  changed_by: string | null;
  notes: string | null;
  changed_at: string;
}

export interface FeedbackData {
  rating: number;
  comments: string;
}

export const complaintsAPI = {
  submit: async (data: ComplaintSubmission): Promise<Complaint> => {
    const response = await apiClient.post('/complaints', data);
    return response.data;
  },

  getById: async (id: string): Promise<Complaint> => {
    const response = await apiClient.get(`/complaints/${id}`);
    return response.data;
  },

  getHistory: async (id: string): Promise<StatusHistory[]> => {
    const response = await apiClient.get(`/complaints/${id}/history`);
    return response.data.history || [];
  },

  getUserComplaints: async (userId: string): Promise<Complaint[]> => {
    const response = await apiClient.get(`/complaints/user/${userId}`);
    console.log('API Response:', response.data);
    // Backend returns { user_id, total_complaints, complaints: [...] }
    if (response.data.complaints) {
      return response.data.complaints;
    }
    // Fallback if response is already an array
    if (Array.isArray(response.data)) {
      return response.data;
    }
    // If neither, return empty array
    return [];
  },

  submitFeedback: async (id: string, data: FeedbackData): Promise<void> => {
    await apiClient.post(`/complaints/${id}/feedback`, data);
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/complaints/${id}`);
  },
};
