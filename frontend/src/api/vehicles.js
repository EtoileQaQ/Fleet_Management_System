import apiClient from './client';

export const vehiclesApi = {
  list: async (params = {}) => {
    const response = await apiClient.get('/vehicles', { params });
    return response.data;
  },
  
  get: async (id) => {
    const response = await apiClient.get(`/vehicles/${id}`);
    return response.data;
  },
  
  create: async (data) => {
    const response = await apiClient.post('/vehicles', data);
    return response.data;
  },
  
  update: async (id, data) => {
    const response = await apiClient.put(`/vehicles/${id}`, data);
    return response.data;
  },
  
  delete: async (id) => {
    await apiClient.delete(`/vehicles/${id}`);
  },
  
  updateStatus: async (id, status) => {
    const response = await apiClient.patch(`/vehicles/${id}/status?new_status=${status}`);
    return response.data;
  },
};



