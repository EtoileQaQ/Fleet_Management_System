import apiClient from './client';

export const authApi = {
  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await apiClient.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  
  loginJson: async (email, password) => {
    const response = await apiClient.post('/auth/login/json', { email, password });
    return response.data;
  },
  
  refresh: async (refreshToken) => {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
  
  setup: async (email, password) => {
    const response = await apiClient.post('/auth/setup', {
      email,
      password,
      role: 'ADMIN',
    });
    return response.data;
  },
};



