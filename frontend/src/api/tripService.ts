import { apiClient } from './client';
import { Trip, TripCreate, TripUpdate, TripListResponse } from '../types/trip';

export const tripService = {
  createTrip: async (data: TripCreate): Promise<Trip> => {
    const response = await apiClient.post<Trip>('/trips/', data);
    return response.data;
  },

  listTrips: async (page: number = 1, pageSize: number = 10, status?: string): Promise<TripListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...(status && { status }),
    });
    const response = await apiClient.get<TripListResponse>(`/trips/?${params}`);
    return response.data;
  },

  getTrip: async (id: number): Promise<Trip> => {
    const response = await apiClient.get<Trip>(`/trips/${id}`);
    return response.data;
  },

  updateTrip: async (id: number, data: TripUpdate): Promise<Trip> => {
    const response = await apiClient.patch<Trip>(`/trips/${id}`, data);
    return response.data;
  },

  deleteTrip: async (id: number): Promise<void> => {
    await apiClient.delete(`/trips/${id}`);
  },
}; 