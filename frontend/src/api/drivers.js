import apiClient from './client';

export const driversApi = {
  list: async (params = {}) => {
    const response = await apiClient.get('/drivers', { params });
    return response.data;
  },
  
  get: async (id) => {
    const response = await apiClient.get(`/drivers/${id}`);
    return response.data;
  },
  
  create: async (data) => {
    const response = await apiClient.post('/drivers', data);
    return response.data;
  },
  
  update: async (id, data) => {
    const response = await apiClient.put(`/drivers/${id}`, data);
    return response.data;
  },
  
  delete: async (id) => {
    await apiClient.delete(`/drivers/${id}`);
  },
  
  assignVehicle: async (driverId, vehicleId) => {
    const response = await apiClient.post(`/drivers/${driverId}/assign-vehicle/${vehicleId}`);
    return response.data;
  },
  
  unassignVehicle: async (driverId) => {
    const response = await apiClient.post(`/drivers/${driverId}/unassign-vehicle`);
    return response.data;
  },
};



