# Emergency Information for {{ destination }}

## Emergency Contacts
{% for service, number in emergency_contacts.items() %}
- {{ service|title }}: {{ number }}
{% endfor %}

## Medical Facilities
{% for facility in medical_facilities %}
### {{ facility.name }}
- Address: {{ facility.address }}
- Phone: {{ facility.phone }}
- Hours: {{ facility.hours }}
- Specialties: {{ facility.specialties|join(', ') }}
- Languages: {{ facility.languages|join(', ') }}
{% endfor %}

## Embassy/Consulate Information
{% if embassy_info %}
- Address: {{ embassy_info.address }}
- Phone: {{ embassy_info.phone }}
- Email: {{ embassy_info.email|default('Not provided') }}
- Services: {{ embassy_info.services|join(', ')|default('Contact embassy for details') }}
{% endif %}

## Important Local Information
{% if local_info %}
### Police Stations
{% for station in local_info.police_stations %}
- {{ station.name }}: {{ station.address }} ({{ station.phone }})
{% endfor %}

### 24/7 Pharmacies
{% for pharmacy in local_info.pharmacies %}
- {{ pharmacy.name }}: {{ pharmacy.address }} ({{ pharmacy.phone }})
{% endfor %}
{% endif %}

## Emergency Phrases
{% if emergency_phrases %}
{% for phrase in emergency_phrases %}
- {{ phrase.local }}: {{ phrase.english }}
{% endfor %}
{% endif %}

## Insurance Information
{% if insurance %}
- Provider: {{ insurance.provider }}
- Policy Number: {{ insurance.policy_number }}
- Emergency Contact: {{ insurance.emergency_contact }}
- How to File a Claim: {{ insurance.claim_instructions }}
{% endif %}

## Emergency Procedures
### Medical Emergency
1. Call emergency services (see numbers above)
2. Contact your insurance provider
3. Notify embassy/consulate if needed
4. Keep all medical documentation

### Natural Disasters
{% if disaster_procedures %}
{{ disaster_procedures }}
{% endif %}

## Important Documents
- Keep copies of passport
- Insurance cards
- Emergency contacts list
- Local embassy contact information

## Local Emergency Apps
{% if emergency_apps %}
{% for app in emergency_apps %}
### {{ app.name }}
- Purpose: {{ app.purpose }}
- Download: {{ app.download_link }}
{% endfor %}
{% endif %}

*Last Updated: {{ last_updated|default('Not specified') }}* 