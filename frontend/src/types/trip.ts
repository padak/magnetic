export interface TripPreferences {
  interests: string[];
  budget: string;
  accommodation_type?: string;
  travel_style?: string;
  accessibility_needs?: string[];
  dietary_restrictions?: string[];
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

export interface TripBudget {
  total: number;
  spent: number;
  currency: string;
  breakdown: Record<string, number>;
}

export interface TripDates {
  start: string;
  end: string;
}

export interface TripDocument {
  path: string;
  type: "itinerary" | "guide" | "emergency" | "checklist";
  last_updated: string;
}

export interface WeatherUpdate {
  temperature: number;
  conditions: string;
  timestamp: string;
}

export interface TravelAlert {
  type: string;
  message: string;
  severity: "info" | "warning" | "critical";
  timestamp: string;
}

export interface TripMonitoring {
  weather_updates: WeatherUpdate[];
  travel_alerts?: TravelAlert[];
}

export interface Trip {
  id: number;
  title: string;
  description: string;
  destination: string;
  start_date: string;
  end_date: string;
  status: "planning" | "planned" | "in_progress" | "completed";
  preferences: TripPreferences;
  budget?: TripBudget;
  documents?: TripDocument[];
  monitoring?: TripMonitoring;
  created_at: string;
  updated_at: string;
}

export interface TripCreate {
  title: string;
  description: string;
  destination: string;
  start_date: string;
  end_date: string;
  preferences: TripPreferences;
}

export interface TripUpdate {
  title?: string;
  description?: string;
  preferences?: Partial<TripPreferences>;
}

export interface TripListResponse {
  trips: Trip[];
  total: number;
  page: number;
  page_size: number;
}