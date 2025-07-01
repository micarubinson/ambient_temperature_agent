"""
Configuration settings for the ambient temperature agent.
Uses environment variables for API keys and configuration.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Settings:
    """Configuration settings for the ambient temperature agent."""
    
    # WeatherAPI Configuration
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "YOUR_WEATHER_API_KEY_HERE")
    WEATHER_API_BASE_URL: str = "http://api.weatherapi.com/v1"
    
    # OpenAI Configuration (supports multiple providers)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY_HERE")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "YOUR_AZURE_OPENAI_API_KEY_HERE")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "YOUR_AZURE_OPENAI_ENDPOINT_HERE")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    # LLM Configuration
    LOCATION_AGENT_TEMPERATURE: float = 0.0  # Zero temperature for consistent, factual location extraction
    WEATHER_AGENT_TEMPERATURE: float = 0.0   # Zero temperature to avoid hallucinations in weather responses
    
    # Confidence Thresholds
    MIN_LOCATION_CONFIDENCE: float = 0.3
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
    
    # Test Configuration
    TEST_EQUIPMENT_ID: str = "PUMP_001_NYC"
    
    @classmethod
    def get_weather_api_url(cls, endpoint: str) -> str:
        """Get full WeatherAPI URL for a specific endpoint."""
        return f"{cls.WEATHER_API_BASE_URL}/{endpoint}"
    
    @classmethod
    def is_azure_openai_configured(cls) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return bool(cls.AZURE_OPENAI_API_KEY and cls.AZURE_OPENAI_ENDPOINT)
    
    @classmethod
    def is_openai_configured(cls) -> bool:
        """Check if OpenAI is properly configured."""
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE")
    
    @classmethod
    def is_weather_api_configured(cls) -> bool:
        """Check if WeatherAPI is properly configured."""
        return bool(cls.WEATHER_API_KEY and cls.WEATHER_API_KEY != "YOUR_WEATHER_API_KEY_HERE")
    
    @classmethod
    def validate_configuration(cls) -> list:
        """
        Validate that required configuration is present.
        
        Returns:
            List of missing configuration items
        """
        missing = []
        
        if not cls.is_weather_api_configured():
            missing.append("WEATHER_API_KEY")
        
        if not cls.is_openai_configured() and not cls.is_azure_openai_configured():
            missing.append("OPENAI_API_KEY or Azure OpenAI configuration")
        
        return missing


# Global settings instance
settings = Settings() 