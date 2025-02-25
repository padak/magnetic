"""FileSurfer agent implementation using Magentic-One framework."""

import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
from fpdf import FPDF
import jinja2
import markdown
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jinja2 import Environment, FileSystemLoader

# Import directly from OpenAI instead of autogen_ext.models.openai
import openai
from openai import OpenAI
from autogen_ext.teams.magentic_one import MagenticOne
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

# Import LLM client factory
from .orchestrator_m1 import LLMClientFactory

class FileSystemHandler(FileSystemEventHandler):
    """Handler for file system events."""
    
    def __init__(self, callback):
        """Initialize the handler with a callback function."""
        self.callback = callback
        
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self.callback(event.src_path, 'modified')
            
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self.callback(event.src_path, 'created')
            
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            self.callback(event.src_path, 'deleted')

class FileSurferM1:
    """FileSurfer agent using Magentic-One framework."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, templates_dir: Optional[str] = None, output_dir: Optional[str] = None):
        """Initialize the FileSurfer agent.
        
        Args:
            config: Optional configuration dictionary
            templates_dir: Directory containing document templates
            output_dir: Directory for generated documents
        """
        self.config = config or {}
        
        # Get LLM provider from config or default to OpenAI
        llm_provider = self.config.get('llm_provider', 'openai')
        llm_config = self.config.get('llm_config', {})
        
        # Create LLM client using factory
        self.client_config = LLMClientFactory.create_client(llm_provider, llm_config)
        
        # Create OpenAI client directly if needed
        if llm_provider == "openai":
            self.client = self.client_config["client"]
        elif llm_provider == "anthropic":
            self.client = self.client_config["client"]
        else:
            self.client = self.client_config["client"]
        
        self.code_executor = LocalCommandLineCodeExecutor()
        self.m1 = MagenticOne(
            client=self.client,
            code_executor=self.code_executor
        )
        
        # Set up template and output directories
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), '../../templates')
        self.output_dir = output_dir or os.path.join(os.path.dirname(__file__), '../../output')
        
        # Ensure directories exist
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Set up file monitoring
        self.observer = None
        
        # Initialize file system observer
        self.observer = Observer()
        self.handler = FileSystemHandler(self._handle_file_event)
        self.observer.schedule(self.handler, str(self.output_dir), recursive=False)
        self.observer.start()
        
    async def create_document(self, template_name: str, data: Dict, output_format: str = 'markdown') -> str:
        """Create a document from a template.
        
        Args:
            template_name: Name of the template file
            data: Data to populate the template
            output_format: Output format ('markdown' or 'pdf')
            
        Returns:
            Path to the generated document
        """
        # Get template
        template = self.jinja_env.get_template(template_name)
        
        # Render template
        rendered = template.render(**data)
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = template_name.replace('.md', '')
        output_name = f"{base_name}_{timestamp}"
        
        if output_format == 'pdf':
            # Convert markdown to PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            
            # Convert markdown to HTML and write to PDF
            html = markdown.markdown(rendered)
            pdf.write_html(html)
            
            # Save PDF
            output_path = self.output_dir / f"{output_name}.pdf"
            pdf.output(str(output_path))
        else:
            # Save as markdown
            output_path = self.output_dir / f"{output_name}.md"
            output_path.write_text(rendered)
            
        return str(output_path)
        
    async def create_itinerary(self, trip_data: Dict) -> str:
        """Create a trip itinerary document.
        
        Args:
            trip_data: Dictionary containing trip details
            
        Returns:
            Path to the generated itinerary
        """
        # Use Magentic-One to enhance itinerary data
        enhanced_data = await self.m1.run_stream(
            "Enhance the trip data with additional details for the itinerary",
            trip_data
        )
        
        template_name = 'itinerary_template.md'
        return await self.create_document(template_name, enhanced_data)
        
    async def create_travel_guide(self, destination: str, interests: List[str]) -> str:
        """Create a travel guide document.
        
        Args:
            destination: Name of the destination
            interests: List of traveler interests
            
        Returns:
            Path to the generated guide
        """
        # Use Magentic-One to generate guide content
        self.m1.messages = [{"role": "user", "content": json.dumps({
            'task': "Generate a comprehensive travel guide",
            'destination': destination,
            'interests': interests
        })}]
        
        try:
            guide_data = ""
            async for chunk in self.m1.run_stream():
                guide_data += chunk
            
            # Parse the response and format it for the template
            response = json.loads(guide_data)
            template_data = {
                'destination': destination,
                'overview': response.get('message', 'No overview available'),
                'attractions': response.get('attractions', []),
                'local_tips': response.get('local_tips', []),
                'cultural_info': response.get('cultural_info', []),
                'transportation': response.get('transportation', {}),
                'weather': response.get('weather', {}),
                'safety_info': response.get('safety_info', ''),
                'shopping': response.get('shopping', {}),
                'resources': response.get('resources', []),
                'last_updated': datetime.now().isoformat()
            }
            
            template_name = 'guide_template.md'
            return await self.create_document(template_name, template_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse guide data: {e}")
            raise Exception("Failed to generate travel guide: Invalid response format")
        except Exception as e:
            logger.error(f"Error generating travel guide: {e}")
            raise
        
    async def create_emergency_info(self, trip_data: Dict) -> str:
        """Create an emergency information document.
        
        Args:
            trip_data: Dictionary containing trip details
            
        Returns:
            Path to the generated document
        """
        # Use Magentic-One to gather emergency information
        self.m1.messages = [{"role": "user", "content": json.dumps({
            'task': "Gather emergency information for the destination",
            'trip_data': trip_data
        })}]
        
        try:
            emergency_data = ""
            async for chunk in self.m1.run_stream():
                emergency_data += chunk
                
            # Parse the response and format it for the template
            response = json.loads(emergency_data)
            template_data = {
                'destination': trip_data['destination'],
                'emergency_contacts': response.get('emergency_contacts', {}),
                'medical_facilities': response.get('medical_facilities', []),
                'embassy_info': response.get('embassy_info', {}),
                'local_info': response.get('local_info', {}),
                'emergency_phrases': response.get('emergency_phrases', []),
                'insurance': response.get('insurance', {}),
                'disaster_procedures': response.get('disaster_procedures', ''),
                'emergency_apps': response.get('emergency_apps', []),
                'last_updated': datetime.now().isoformat()
            }
            
            template_name = 'emergency_template.md'
            return await self.create_document(template_name, template_data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse emergency info: {e}")
            raise Exception("Failed to generate emergency info: Invalid response format")
        except Exception as e:
            logger.error(f"Error generating emergency info: {e}")
            raise
        
    def monitor_changes(self, file_path: Union[str, Path]) -> None:
        """Monitor a file for changes.
        
        Args:
            file_path: Path to the file to monitor
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
            
        # Add file to watchdog observer
        self.observer.schedule(
            self.handler,
            str(file_path.parent),
            recursive=False
        )
        
    def _handle_file_event(self, file_path: str, event_type: str) -> None:
        """Handle file system events.
        
        Args:
            file_path: Path to the affected file
            event_type: Type of event ('modified', 'created', or 'deleted')
        """
        print(f"File {file_path} was {event_type}")
        
    def __del__(self):
        """Clean up resources."""
        self.observer.stop()
        self.observer.join() 