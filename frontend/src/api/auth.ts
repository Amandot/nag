import apiClient from './client';

export interface RegisterData {
  name: string;
  phone: string;
  email: string;
  password: string;
}

export interface LoginData {
  credential: string;
  password: string;
}

export interface AuthResponse {
  user_id: string;
  token: string;
  name: string;
  email: string;
  role: string;
  message?: string;
}

export const authAPI = {
  register: async (data: RegisterData): Promise<AuthResponse> => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },

  login: async (data: LoginData): Promise<AuthResponse> => {
    const response = await apiClient.post('/auth/login', data);
    // Map access_token to token for consistency
    return {
      ...response.data,
      token: response.data.access_token || response.data.token,
    };
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
  },
};
