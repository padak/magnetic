# {{ destination }} Trip Itinerary

**Dates:** {{ dates.start }} - {{ dates.end }}
**Duration:** {{ (dates.end - dates.start).days }} days

## Daily Schedule

{% for day in daily_schedule %}
### Day {{ loop.index }}: {{ day.date }}

#### Morning
{{ day.morning }}

#### Afternoon
{{ day.afternoon }}

#### Evening
{{ day.evening }}

{% if day.notes %}
**Notes:** {{ day.notes }}
{% endif %}

{% endfor %}

## Recommendations
{% for rec in recommendations %}
- {{ rec }}
{% endfor %}

## Emergency Information
{% if emergency_info %}
### Emergency Contacts
- Police: {{ emergency_info.police }}
- Hospital: {{ emergency_info.hospital }}
{% if emergency_info.embassy %}
- Embassy: {{ emergency_info.embassy }}
{% endif %}

### Important Notes
{% for note in emergency_info.notes %}
- {{ note }}
{% endfor %}
{% endif %} 