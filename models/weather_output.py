"""
Pydantic model for weather agent output.
Defines the structured output format for weather data retrieval.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class WeatherOutput(BaseModel):
    """
    Structured output model for weather data retrieval.
    
    This model defines the expected output format from the weather agent
    that retrieves current temperature data for a given location.
    """
    
    location_used: str = Field(
        description="The location string that was used to query the weather API"
    )
    
    current_temperature_celsius: Optional[float] = Field(
        default=None,
        description="Current temperature in Celsius. None if weather data unavailable."
    )
    
    current_temperature_fahrenheit: Optional[float] = Field(
        default=None,
        description="Current temperature in Fahrenheit. None if weather data unavailable."
    )
    
    weather_condition: Optional[str] = Field(
        default=None,
        description="Current weather condition description (e.g., 'Sunny', 'Cloudy', 'Rain')"
    )
    
    humidity: Optional[int] = Field(
        default=None,
        description="Current humidity percentage (0-100)"
    )
    
    wind_speed_kph: Optional[float] = Field(
        default=None,
        description="Current wind speed in kilometers per hour"
    )
    
    api_success: bool = Field(
        description="Whether the weather API call was successful"
    )
    
    api_error: Optional[str] = Field(
        default=None,
        description="Error message if API call failed"
    )
    
    data_source: str = Field(
        description="Source of weather data (e.g., 'WeatherAPI.com')"
    )
    
    timestamp: str = Field(
        description="Timestamp when weather data was retrieved (ISO format)"
    )
    
    @validator('current_temperature_celsius')
    def validate_celsius_range(cls, v):
        """Validate temperature is within reasonable range."""
        if v is not None and not -100 <= v <= 60:
            raise ValueError('Temperature in Celsius must be between -100 and 60')
        return v
    
    @validator('current_temperature_fahrenheit')
    def validate_fahrenheit_range(cls, v):
        """Validate temperature is within reasonable range."""
        if v is not None and not -148 <= v <= 140:
            raise ValueError('Temperature in Fahrenheit must be between -148 and 140')
        return v
    
    @validator('humidity')
    def validate_humidity_range(cls, v):
        """Validate humidity is within valid percentage range."""
        if v is not None and not 0 <= v <= 100:
            raise ValueError('Humidity must be between 0 and 100')
        return v
    
    def has_temperature_data(self) -> bool:
        """Check if temperature data is available."""
        return self.current_temperature_celsius is not None
    
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
            return f"{self.current_temperature_celsius}°C"
        elif unit == "fahrenheit":
            return f"{self.current_temperature_fahrenheit}°F"
        else:  # both
            return f"{self.current_temperature_celsius}°C ({self.current_temperature_fahrenheit}°F)" 