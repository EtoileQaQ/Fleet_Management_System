import apiClient from './client';

export const tachographApi = {
  upload: async (file, driverId, vehicleId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('driver_id', driverId);
    if (vehicleId) {
      formData.append('vehicle_id', vehicleId);
    }
    
    const response = await apiClient.post('/tachograph/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  
  getActivities: async (driverId, params = {}) => {
    const response = await apiClient.get(`/tachograph/activities/${driverId}`, { params });
    return response.data;
  },
  
  getSummary: async (driverId, startDate, endDate) => {
    const response = await apiClient.get(`/tachograph/summary/${driverId}`, {
      params: { start_date: startDate, end_date: endDate }
    });
    return response.data;
  },
};


