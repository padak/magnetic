import axios from 'axios';
import { Trip, TripCreate, TripUpdate, TripListResponse } from '../types/trip';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const tripApi = {
  createTrip: async (data: TripCreate): Promise<Trip> => {
    const response = await apiClient.post<Trip>('/trips', data);
    return response.data;
  },

  listTrips: async (page: number = 1, pageSize: number = 10): Promise<TripListResponse> => {
    const response = await apiClient.get<TripListResponse>('/trips', {
      params: { page, page_size: pageSize },
    });
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

export default apiClient; 