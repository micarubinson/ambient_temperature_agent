"""
Pydantic model for the final ambient temperature agent response.
Combines location and weather information into the required format.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from models.location_output import LocationOutput
from models.weather_output import WeatherOutput


class FinalResponse(BaseModel):
    """
    Final response model for the ambient temperature agent.
    
    Combines location and weather information into the required format:
    "Industrial equipment {equipment_id} is located in {location} and the temperature in this location is {temperature}"
    """
    
    equipment_id: str = Field(
        description="The equipment ID that was queried"
    )
    
    location: str = Field(
        description="The determined location of the equipment"
    )
    
    temperature_celsius: Optional[float] = Field(
        default=None,
        description="Current temperature in Celsius. None if temperature unavailable."
    )
    
    temperature_fahrenheit: Optional[float] = Field(
        default=None,
        description="Current temperature in Fahrenheit. None if temperature unavailable."
    )
    
    weather_condition: Optional[str] = Field(
        default=None,
        description="Current weather condition description"
    )
    
    formatted_response: str = Field(
        description="The final formatted response as specified in project rules"
    )
    
    # Metadata for debugging and monitoring
    location_confidence: float = Field(
        description="Confidence level of location determination"
    )
    
    location_has_conflict: bool = Field(
        description="Whether location conflicts were detected"
    )
    
    weather_api_success: bool = Field(
        description="Whether weather API call was successful"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if any step failed"
    )
    
    timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp when weather data was retrieved (ISO format)"
    )
    
    @classmethod
    def create_success_response(
        cls, 
        equipment_id: str, 
        location_output: LocationOutput,
        weather_output: WeatherOutput
    ) -> "FinalResponse":
        """
        Create a successful response from location and weather outputs.
        
        Args:
            equipment_id: The equipment ID
            location_output: Output from location agent
            weather_output: Output from weather agent
            
        Returns:
            FinalResponse instance with formatted response
        """
        # Create formatted response based on whether temperature is available
        if weather_output.has_temperature_data():
            formatted_response = (
                f"Industrial equipment {equipment_id} is located in {location_output.location} "
                f"and the temperature in this location is {weather_output.current_temperature_celsius}°C"
            )
        else:
            formatted_response = (
                f"Industrial equipment {equipment_id} is located in {location_output.location} "
                f"but the temperature in this location is unavailable"
            )
        
        return cls(
            equipment_id=equipment_id,
            location=location_output.location,
            temperature_celsius=weather_output.current_temperature_celsius,
            temperature_fahrenheit=weather_output.current_temperature_fahrenheit,
            weather_condition=weather_output.weather_condition,
            formatted_response=formatted_response,
            location_confidence=location_output.confidence,
            location_has_conflict=location_output.has_location_conflict,
            weather_api_success=weather_output.api_success,
            timestamp=weather_output.timestamp
        )
    
    @classmethod
    def create_error_response(
        cls,
        equipment_id: str,
        error_message: str,
        location_output: Optional[LocationOutput] = None
    ) -> "FinalResponse":
        """
        Create an error response when the process fails.
        
        Args:
            equipment_id: The equipment ID
            error_message: Description of the error
            location_output: Optional location output if available
            
        Returns:
            FinalResponse instance with error information
        """
        location = location_output.location if location_output else "unknown location"
        
        formatted_response = (
            f"Industrial equipment {equipment_id} could not be processed: {error_message}"
        )
        
        return cls(
            equipment_id=equipment_id,
            location=location,
            formatted_response=formatted_response,
            location_confidence=location_output.confidence if location_output else 0.0,
            location_has_conflict=location_output.has_location_conflict if location_output else False,
            weather_api_success=False,
            error_message=error_message
        )
    
    def has_temperature_data(self) -> bool:
        """Check if temperature data is available."""
        return self.temperature_celsius is not None
    
    def get_temperature_display(self, unit: str = "both") -> str:
        """
        Get formatted temperature string for display.
        
        Args:
            unit: "celsius", "fahrenheit", or "both"
            
        Returns:
            Formatted temperature string
        """
        if not self.has_temperature_data():
            return "Temperature data unavailable"
        
        if unit == "celsius":
            return f"{self.temperature_celsius}°C"
        elif unit == "fahrenheit":
            return f"{self.temperature_fahrenheit}°F"
        else:  # both
            return f"{self.temperature_celsius}°C ({self.temperature_fahrenheit}°F)" 