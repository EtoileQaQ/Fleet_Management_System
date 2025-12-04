import apiClient from './client';

export const telematicsApi = {
  getVehicleStatus: async (vehicleId) => {
    const response = await apiClient.get(`/telematics/status/${vehicleId}`);
    return response.data;
  },
  
  getAllVehiclesStatus: async () => {
    const response = await apiClient.get('/telematics/status');
    return response.data;
  },
  
  getOnlineStats: async () => {
    const response = await apiClient.get('/telematics/stats/online');
    return response.data;
  },
  
  sendPosition: async (position) => {
    const response = await apiClient.post('/telematics/position', position);
    return response.data;
  },
};


