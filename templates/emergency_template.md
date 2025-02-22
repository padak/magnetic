# Emergency Information for {{ destination }}

## Emergency Contacts

### Local Emergency Numbers
{% for contact in emergency_contacts %}
- {{ contact.name }}: {{ contact.number }}
{% endfor %}

### Medical Facilities
{% for facility in medical_facilities %}
### {{ facility.name }}
**Address:** {{ facility.address }}
**Phone:** {{ facility.phone }}
**Hours:** {{ facility.hours }}
**Specialties:** {{ facility.specialties }}
**Languages:** {{ facility.languages }}

{% endfor %}

### Embassy/Consulate Information
{% if embassy_info %}
#### {{ embassy_info.country }} Embassy
**Address:** {{ embassy_info.address }}
**Phone:** {{ embassy_info.phone }}
**Emergency Line:** {{ embassy_info.emergency_line }}
**Email:** {{ embassy_info.email }}
**Hours:** {{ embassy_info.hours }}

**Services:**
{% for service in embassy_info.services %}
- {{ service }}
{% endfor %}
{% endif %}

## Important Local Information

### Police Stations
{% for station in police_stations %}
### {{ station.name }}
**Address:** {{ station.address }}
**Phone:** {{ station.phone }}
**District:** {{ station.district }}

{% endfor %}

### Pharmacies
{% for pharmacy in pharmacies %}
### {{ pharmacy.name }}
**Address:** {{ pharmacy.address }}
**Phone:** {{ pharmacy.phone }}
**Hours:** {{ pharmacy.hours }}
**24/7:** {{ "Yes" if pharmacy.is_24h else "No" }}

{% endfor %}

## Emergency Phrases
{% for phrase in emergency_phrases %}
- {{ phrase.local }}: {{ phrase.english }}
{% endfor %}

## Insurance Information
{% if insurance_info %}
### Travel Insurance
**Provider:** {{ insurance_info.provider }}
**Policy Number:** {{ insurance_info.policy_number }}
**Coverage:** {{ insurance_info.coverage }}
**24/7 Assistance:** {{ insurance_info.assistance_line }}

**How to File a Claim:**
{% for step in insurance_info.claim_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}
{% endif %}

## Emergency Procedures

### Medical Emergency
{% for step in medical_emergency_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

### Natural Disasters
{% for disaster in natural_disaster_procedures %}
### {{ disaster.type }}
{% for step in disaster.steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

{% endfor %}

## Important Documents
Keep copies of these documents in a safe place:
{% for doc in important_documents %}
- {{ doc }}
{% endfor %}

## Local Emergency Apps
{% for app in emergency_apps %}
### {{ app.name }}
**Purpose:** {{ app.purpose }}
**Download:** {{ app.download_link }}
**Languages:** {{ app.languages }}

{% endfor %} 