# Estimations based on research and general averages. Update as necessary.
accommodation_per_night = 200  # Average price per night for a family-friendly hotel
meals_per_day = 100  # Average cost of meals per day for a family
transport_per_day = 50  # Average daily cost for public transport and taxis
attraction_entry_per_day = 120  # Average cost of entry fees to attractions per day

# Constants
days = 5

# Simple budget calculator
total_accommodation_cost = accommodation_per_night * days
total_meals_cost = meals_per_day * days
total_transport_cost = transport_per_day * days
total_attraction_cost = attraction_entry_per_day * days

grand_total_cost = total_accommodation_cost + total_meals_cost + total_transport_cost + total_attraction_cost

print("Estimated Travel Budget for 5-Day Trip to Boston:")
print(f"Total Accommodation: ${total_accommodation_cost}")
print(f"Total Meals: ${total_meals_cost}")
print(f"Total Transport: ${total_transport_cost}")
print(f"Total Attraction Entry Fees: ${total_attraction_cost}")
print(f"Grand Total Estimated Cost: ${grand_total_cost}")
