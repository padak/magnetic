"""Tests for the Magentic-One FileSurfer implementation."""

import pytest
import pytest_asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import tempfile
import shutil
import os
import asyncio

from magnetic.agents.filesurfer_m1 import FileSurferM1
from autogen_ext.teams.magentic_one import MagenticOne

@pytest_asyncio.fixture
async def filesurfer():
    """Create a FileSurfer instance for testing."""
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        templates_dir = Path(temp_dir) / "templates"
        output_dir = Path(temp_dir) / "output"
        templates_dir.mkdir()
        output_dir.mkdir()
        
        # Create test templates
        itinerary_template = """# Trip Itinerary

Destination: {{ destination }}
Dates: {{ dates.start }} - {{ dates.end }}

## Daily Schedule
{% for day in daily_schedule %}
### Day {{ loop.index }}
{{ day.activities }}
{% endfor %}
"""
        guide_template = """# Travel Guide: {{ destination }}

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
"""
        emergency_template = """# Emergency Information for {{ destination }}

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
"""
        
        # Write templates to files
        (templates_dir / "itinerary_template.md").write_text(itinerary_template)
        (templates_dir / "guide_template.md").write_text(guide_template)
        (templates_dir / "emergency_template.md").write_text(emergency_template)
        
        with patch('autogen_ext.teams.magentic_one.MagenticOne') as mock_m1_class:
            # Configure mock M1
            mock_m1 = AsyncMock()
            mock_m1_class.return_value = mock_m1
            
            # Create FileSurfer instance
            agent = FileSurferM1(
                m1=mock_m1,
                templates_dir=str(templates_dir),
                output_dir=str(output_dir)
            )
            
            yield agent

@pytest.mark.asyncio
async def test_create_document_markdown(filesurfer):
    """Test creating a markdown document."""
    data = {
        'destination': 'Boston',
        'dates': {
            'start': '2025-03-01',
            'end': '2025-03-05'
        },
        'daily_schedule': [
            {'activities': 'Visit Freedom Trail'},
            {'activities': 'Explore Faneuil Hall'}
        ]
    }
    
    output_path = await filesurfer.create_document(
        'itinerary_template.md',
        data,
        output_format='markdown'
    )
    
    assert output_path.endswith('.md')
    assert os.path.exists(output_path)
    
    # Verify content
    content = Path(output_path).read_text()
    assert 'Boston' in content
    assert '2025-03-01' in content
    assert 'Freedom Trail' in content

@pytest.mark.asyncio
async def test_create_document_pdf(filesurfer):
    """Test creating a PDF document."""
    data = {
        'destination': 'Boston',
        'dates': {
            'start': '2025-03-01',
            'end': '2025-03-05'
        },
        'daily_schedule': [
            {'activities': 'Visit Freedom Trail'},
            {'activities': 'Explore Faneuil Hall'}
        ]
    }
    
    output_path = await filesurfer.create_document(
        'itinerary_template.md',
        data,
        output_format='pdf'
    )
    
    assert output_path.endswith('.pdf')
    assert os.path.exists(output_path)

@pytest.mark.asyncio
async def test_create_itinerary(filesurfer):
    """Test creating a trip itinerary."""
    trip_data = {
        'destination': 'Boston',
        'dates': {
            'start': '2025-03-01',
            'end': '2025-03-05'
        }
    }
    
    # Mock Magentic-One response
    enhanced_data = {
        'destination': 'Boston',
        'dates': trip_data['dates'],
        'daily_schedule': [
            {'activities': 'Visit Freedom Trail'},
            {'activities': 'Explore Faneuil Hall'}
        ]
    }
    filesurfer.m1.run_stream = AsyncMock(return_value=enhanced_data)
    
    output_path = await filesurfer.create_itinerary(trip_data)
    
    assert output_path.endswith('.md')
    assert os.path.exists(output_path)
    
    # Verify Magentic-One was called
    filesurfer.m1.run_stream.assert_called_once()

@pytest.mark.asyncio
async def test_create_travel_guide(filesurfer):
    """Test creating a travel guide."""
    # Mock Magentic-One response
    guide_data = {
        'destination': 'Boston',
        'attractions': ['Freedom Trail', 'Fenway Park'],
        'local_tips': ['Use the T for transportation', 'Visit during fall'],
        'cultural_info': ['Rich colonial history', 'Strong academic presence']
    }
    filesurfer.m1.run_stream = AsyncMock(return_value=guide_data)
    
    output_path = await filesurfer.create_travel_guide(
        destination='Boston',
        interests=['history', 'sports']
    )
    
    assert output_path.endswith('.md')
    assert os.path.exists(output_path)
    
    # Verify Magentic-One was called
    filesurfer.m1.run_stream.assert_called_once()

@pytest.mark.asyncio
async def test_create_emergency_info(filesurfer):
    """Test creating emergency information document."""
    trip_data = {
        'destination': 'Boston',
        'dates': {
            'start': '2025-03-01',
            'end': '2025-03-05'
        }
    }
    
    # Mock Magentic-One response
    emergency_data = {
        'emergency_contacts': {'police': '911', 'ambulance': '911'},
        'medical_facilities': [
            {
                'name': 'Mass General Hospital',
                'address': '55 Fruit Street',
                'phone': '+1-617-726-2000',
                'hours': '24/7',
                'specialties': ['Emergency', 'Trauma'],
                'languages': ['English', 'Spanish']
            }
        ],
        'embassy_info': {
            'address': '123 Main St',
            'phone': '+1-555-0123',
            'email': 'embassy@example.com',
            'services': ['Passport Services', 'Emergency Assistance']
        }
    }
    filesurfer.m1.run_stream = AsyncMock(return_value=emergency_data)
    
    output_path = await filesurfer.create_emergency_info(trip_data)
    
    assert output_path.endswith('.md')
    assert os.path.exists(output_path)
    
    # Verify Magentic-One was called
    filesurfer.m1.run_stream.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_changes(filesurfer):
    """Test monitoring file changes."""
    # Create a temporary file to monitor
    temp_file = filesurfer.output_dir / "test.txt"
    temp_file.write_text("Initial content")
    
    # Start monitoring
    filesurfer.monitor_changes(str(temp_file))
    
    # Modify the file
    temp_file.write_text("Modified content")
    
    # Wait for event to be processed
    await asyncio.sleep(0.1)

@pytest.mark.asyncio
async def test_monitor_changes_nonexistent_file(filesurfer):
    """Test monitoring a nonexistent file."""
    with pytest.raises(ValueError):
        filesurfer.monitor_changes("nonexistent.txt") 