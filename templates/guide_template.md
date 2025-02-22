# {{ destination }} Travel Guide

## Overview
{{ overview }}

## Must-See Attractions
{% for attraction in attractions %}
### {{ attraction.name }}
{{ attraction.description }}

**Location:** {{ attraction.location }}
**Hours:** {{ attraction.hours }}
**Tips:** {{ attraction.tips }}

{% endfor %}

## Local Tips
{% for tip in local_tips %}
- {{ tip }}
{% endfor %}

## Cultural Information
{{ cultural_info.overview }}

### Customs and Etiquette
{% for custom in cultural_info.customs %}
- {{ custom }}
{% endfor %}

### Local Cuisine
{% for food in cultural_info.cuisine %}
### {{ food.name }}
{{ food.description }}
**Where to try:** {{ food.recommendations }}

{% endfor %}

## Transportation
{{ transportation.overview }}

### Getting Around
{% for mode in transportation.modes %}
#### {{ mode.name }}
{{ mode.description }}
**Cost:** {{ mode.cost }}
**Tips:** {{ mode.tips }}

{% endfor %}

## Weather and Best Time to Visit
{{ weather.overview }}

### Seasonal Information
{% for season in weather.seasons %}
#### {{ season.name }}
{{ season.description }}
**Average Temperature:** {{ season.temperature }}
**What to Pack:** {{ season.packing_tips }}

{% endfor %}

## Safety Information
{{ safety.overview }}

### Important Numbers
{% for number in safety.emergency_numbers %}
- {{ number.name }}: {{ number.number }}
{% endfor %}

### Areas to Avoid
{% for area in safety.areas_to_avoid %}
- {{ area }}
{% endfor %}

## Shopping
{{ shopping.overview }}

### Popular Markets and Shops
{% for shop in shopping.recommendations %}
### {{ shop.name }}
{{ shop.description }}
**Location:** {{ shop.location }}
**Best For:** {{ shop.specialties }}

{% endfor %}

## Additional Resources
{% for resource in additional_resources %}
- {{ resource.name }}: {{ resource.link }}
{% endfor %} 