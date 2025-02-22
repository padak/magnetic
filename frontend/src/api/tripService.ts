import { apiClient } from './client';
import { Trip, TripCreate, TripUpdate, TripListResponse, TripDocument, TripMonitoring } from '../types/trip';

export const tripService = {
  createTrip: async (data: TripCreate): Promise<Trip> => {
    const response = await apiClient.post<Trip>('/api/trips/', data);
    return response.data;
  },

  listTrips: async (page: number = 1, pageSize: number = 10, status?: string): Promise<TripListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...(status && { status }),
    });
    const response = await apiClient.get<TripListResponse>(`/api/trips/?${params}`);
    return response.data;
  },

  getTrip: async (id: number): Promise<Trip> => {
    const response = await apiClient.get<Trip>(`/api/trips/${id}`);
    return response.data;
  },

  updateTrip: async (id: number, data: TripUpdate): Promise<Trip> => {
    const response = await apiClient.patch<Trip>(`/api/trips/${id}`, data);
    return response.data;
  },

  deleteTrip: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/trips/${id}`);
  },

  // New methods for M1 features
  getTripDocuments: async (id: number): Promise<TripDocument[]> => {
    const response = await apiClient.get<TripDocument[]>(`/api/trips/${id}/documents`);
    return response.data;
  },

  getMonitoringUpdates: async (id: number): Promise<TripMonitoring> => {
    const response = await apiClient.get<TripMonitoring>(`/api/trips/${id}/monitoring`);
    return response.data;
  },

  startMonitoring: async (id: number, types: string[]): Promise<void> => {
    await apiClient.post(`/api/trips/${id}/monitoring`, { types });
  },

  stopMonitoring: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/trips/${id}/monitoring`);
  }
}; 