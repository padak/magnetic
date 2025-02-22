# Travel Guide: {{ destination }}

## Overview
{{ overview }}

## Must-See Attractions
{% for attraction in attractions %}
- {{ attraction }}
{% endfor %}

## Local Tips
{% for tip in local_tips %}
- {{ tip }}
{% endfor %}

## Cultural Information
{% for info in cultural_info %}
- {{ info }}
{% endfor %}

## Transportation
{% if transportation %}
{% for mode, details in transportation.items() %}
### {{ mode|title }}
{{ details }}
{% endfor %}
{% endif %}

## Weather and Best Time to Visit
{% if weather %}
{{ weather }}
{% endif %}

## Safety Information
{% if safety_info %}
{{ safety_info }}
{% endif %}

## Shopping and Entertainment
{% if shopping %}
{% for area, details in shopping.items() %}
### {{ area }}
{{ details }}
{% endfor %}
{% endif %}

## Additional Resources
{% if resources %}
{% for resource in resources %}
- {{ resource }}
{% endfor %}
{% endif %}

*Last Updated: {{ last_updated|default('Not specified') }}* 