export interface TripPreferences {
  adults: number;
  children: number;
  hotel_budget: string;
  max_activity_price: number;
  activity_types: string[];
  family_friendly: boolean;
  accessible: boolean;
  transportation_budget: number;
  food_budget: number;
  misc_budget: number;
  currency: string;
}

export interface Activity {
  name: string;
  description?: string;
  start_time: string;
  end_time: string;
  location?: string;
  cost: number;
  booking_info: Record<string, any>;
}

export interface Accommodation {
  name: string;
  address: string;
  check_in: string;
  check_out: string;
  cost: number;
  booking_info: Record<string, any>;
}

export interface ItineraryDay {
  date: string;
  notes?: string;
  activities: Activity[];
  accommodation?: Accommodation;
}

export interface Budget {
  total: number;
  spent: number;
  currency: string;
  breakdown: Record<string, number>;
}

export interface Trip {
  id: number;
  title: string;
  description?: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: string;
  preferences: TripPreferences;
  itinerary_days: ItineraryDay[];
  budget?: Budget;
}

export interface TripCreate {
  title: string;
  description?: string;
  destination: string;
  start_date: string;
  end_date: string;
  preferences?: TripPreferences;
}

export interface TripUpdate {
  title?: string;
  description?: string;
  preferences?: TripPreferences;
}

export interface TripListResponse {
  trips: Trip[];
  total: number;
  page: number;
  page_size: number;
}