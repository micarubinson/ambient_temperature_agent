#!/usr/bin/env python3
"""
Main Ambient Temperature Agent Orchestrator.

This is the main entry point for the ambient temperature agent that:
1. Takes an equipment_id as input
2. Extracts location metadata from synthetic dataset
3. Uses LLM to determine equipment location
4. Retrieves weather data for that location
5. Returns formatted response with temperature information

Usage:
    python ambient_temp_agent.py <equipment_id>
    
Example:
    python ambient_temp_agent.py PUMP_001_NYC
"""

import logging
import sys
from typing import Optional

# Project imports
from data.synthetic_extractor import extract_equipment_metadata, list_available_equipment, get_equipment_info
from agents.location_agent import LocationAgent
from agents.weather_agent import WeatherAgent
from models.final_response import FinalResponse
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class AmbientTempAgent:
    """
    Main orchestrator for the ambient temperature agent.
    
    Coordinates the flow from equipment_id to final temperature response
    using synthetic metadata extraction, location analysis, and weather retrieval.
    """
    
    def __init__(self):
        """Initialize the ambient temperature agent with all components."""
        # Validate configuration before initializing agents
        missing_config = settings.validate_configuration()
        if missing_config:
            raise Exception(f"Missing required configuration: {', '.join(missing_config)}")
        
        self.location_agent = LocationAgent()
        self.weather_agent = WeatherAgent()
        logger.info("AmbientTempAgent initialized")
    
    def get_ambient_temperature(self, equipment_id: str) -> FinalResponse:
        """
        Get ambient temperature for an equipment location.
        
        Args:
            equipment_id: The equipment ID to query
            
        Returns:
            FinalResponse with formatted temperature information
        """
        logger.info(f"Starting ambient temperature analysis [equipment_id={equipment_id}]")
        
        location_output = None
        
        try:
            # Step 1: Extract metadata from synthetic dataset
            logger.info(f"Step 1: Extracting metadata [equipment_id={equipment_id}]")
            metadata = extract_equipment_metadata(equipment_id)
            
            if not metadata:
                return FinalResponse.create_error_response(
                    equipment_id=equipment_id,
                    error_message="No metadata found for equipment"
                )
            
            # Step 2: Analyze location from metadata
            logger.info(f"Step 2: Analyzing location [equipment_id={equipment_id}]")
            location_output = self.location_agent.analyze_location(equipment_id, metadata)
            
            if not location_output.location:
                return FinalResponse.create_error_response(
                    equipment_id=equipment_id,
                    error_message="Could not determine equipment location",
                    location_output=location_output
                )
            
            # Step 3: Get weather data for location
            logger.info(f"Step 3: Retrieving weather [equipment_id={equipment_id}] [location={location_output.location}]")
            weather_output = self.weather_agent.get_weather(location_output)
            
            # Step 4: Create final response
            final_response = FinalResponse.create_success_response(
                equipment_id=equipment_id,
                location_output=location_output,
                weather_output=weather_output
            )
            
            logger.info(f"Ambient temperature analysis completed [equipment_id={equipment_id}] [success=True]")
            return final_response
            
        except Exception as e:
            logger.error(f"Ambient temperature analysis failed [equipment_id={equipment_id}] [error={str(e)}]")
            return FinalResponse.create_error_response(
                equipment_id=equipment_id,
                error_message=str(e),
                location_output=location_output
            )


def show_available_equipment():
    """Display all available equipment IDs for user reference."""
    print("\n" + "="*80)
    print("AVAILABLE EQUIPMENT")
    print("="*80)
    
    try:
        equipment_list = list_available_equipment()
        if not equipment_list:
            print("No equipment found in database.")
            return
        
        print(f"Found {len(equipment_list)} pieces of equipment:\n")
        
        for equipment_id in equipment_list:
            info = get_equipment_info(equipment_id)
            print(f"  {info}")
        
        print(f"\nExample usage:")
        print(f"  python ambient_temp_agent.py {equipment_list[0]}")
        
    except Exception as e:
        print(f"Error loading equipment list: {str(e)}")
    
    print("="*80)


def main():
    """Main entry point for command line usage."""
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ["--help", "-h", "help"]):
        print("Usage: python ambient_temp_agent.py <equipment_id>")
        print("       python ambient_temp_agent.py --list     (show available equipment)")
        print(f"Example: python ambient_temp_agent.py {settings.TEST_EQUIPMENT_ID}")
        print("\nFor available equipment IDs, use: python ambient_temp_agent.py --list")
        sys.exit(1)
    
    if len(sys.argv) == 2 and sys.argv[1] in ["--list", "-l", "list"]:
        show_available_equipment()
        sys.exit(0)
    
    if len(sys.argv) != 2:
        print("Usage: python ambient_temp_agent.py <equipment_id>")
        print(f"Example: python ambient_temp_agent.py {settings.TEST_EQUIPMENT_ID}")
        sys.exit(1)
    
    equipment_id = sys.argv[1]
    
    try:
        # Initialize and run the agent
        agent = AmbientTempAgent()
        result = agent.get_ambient_temperature(equipment_id)
        
        # Display results
        print("\n" + "="*80)
        print("AMBIENT TEMPERATURE AGENT RESULTS")
        print("="*80)
        print(f"Equipment ID: {result.equipment_id}")
        print(f"Location: {result.location}")
        print(f"Location Confidence: {result.location_confidence:.2f}")
        print(f"Location Conflicts: {'Yes' if result.location_has_conflict else 'No'}")
        print(f"Weather API Success: {'Yes' if result.weather_api_success else 'No'}")
        
        if result.has_temperature_data():
            print(f"Temperature: {result.get_temperature_display()}")
            if result.weather_condition:
                print(f"Weather Condition: {result.weather_condition}")
            if result.timestamp:
                print(f"Retrieved At: {result.timestamp}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        print("\nFormatted Response:")
        print(f'"{result.formatted_response}"')
        print("="*80)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"\nERROR: {str(e)}")
        print("\nThis might be due to missing configuration. Please check:")
        print("1. WEATHER_API_KEY is set in your environment")
        print("2. OPENAI_API_KEY or Azure OpenAI credentials are configured")
        print("3. Run 'python ambient_temp_agent.py --list' to see available equipment")
        sys.exit(1)


if __name__ == "__main__":
    main() 