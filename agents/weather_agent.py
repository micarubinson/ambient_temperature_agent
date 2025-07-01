"""
Weather LLM Agent using LangGraph for weather data retrieval.
Retrieves current temperature and weather conditions using WeatherAPI.
"""

import logging
from typing import Dict, Any, Optional, TypedDict
import json
import requests
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, END

# LangChain imports
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Project imports
from config.settings import settings
from models.weather_output import WeatherOutput
from models.location_output import LocationOutput

# Configure logging
logger = logging.getLogger(__name__)


class WeatherAgentState(TypedDict):
    """State object for the weather agent graph."""
    location_output: LocationOutput
    weather_output: Optional[WeatherOutput]
    error: Optional[str]
    raw_weather_data: Optional[Dict[str, Any]]


class WeatherAgent:
    """
    LangGraph-based agent for retrieving weather information using WeatherAPI.
    
    Takes location information and retrieves current temperature and weather
    conditions with structured output and error handling.
    """
    
    def __init__(self):
        """Initialize the weather agent with LLM and graph setup."""
        self.llm = self._setup_llm()
        self.output_parser = PydanticOutputParser(pydantic_object=WeatherOutput)
        self.graph = self._build_graph()
        logger.info("WeatherAgent initialized [temperature=0.0]")
    
    def _setup_llm(self):
        """Setup LLM (Azure OpenAI or OpenAI) with zero temperature."""
        if settings.is_azure_openai_configured():
            logger.info("Using Azure OpenAI for weather agent")
            return AzureChatOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                temperature=settings.WEATHER_AGENT_TEMPERATURE
            )
        elif settings.is_openai_configured():
            logger.info("Using OpenAI for weather agent")
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_MODEL,
                temperature=settings.WEATHER_AGENT_TEMPERATURE
            )
        else:
            raise Exception("No LLM configuration found. Please set OPENAI_API_KEY or Azure OpenAI credentials.")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for weather retrieval."""
        graph = StateGraph(WeatherAgentState)
        
        # Add nodes
        graph.add_node("validate_location", self._validate_location_node)
        graph.add_node("fetch_weather", self._fetch_weather_node)
        graph.add_node("process_weather", self._process_weather_node)
        
        # Add edges
        graph.set_entry_point("validate_location")
        graph.add_conditional_edges(
            "validate_location",
            self._should_fetch_weather,
            {
                "fetch": "fetch_weather",
                "error": END
            }
        )
        graph.add_conditional_edges(
            "fetch_weather",
            self._should_process_weather,
            {
                "process": "process_weather",
                "error": END
            }
        )
        graph.add_edge("process_weather", END)
        
        return graph.compile()
    
    def get_weather(self, location_output: LocationOutput) -> WeatherOutput:
        """
        Retrieve weather information for the given location.
        
        Args:
            location_output: LocationOutput from the location agent
            
        Returns:
            WeatherOutput with current weather information
            
        Raises:
            Exception: If weather retrieval fails
        """
        logger.info(f"Starting weather retrieval [location={location_output.location}]")
        
        # Initialize state
        initial_state = WeatherAgentState(
            location_output=location_output,
            weather_output=None,
            error=None,
            raw_weather_data=None
        )
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            if final_state.get("error"):
                raise Exception(final_state["error"])
            
            weather_output = final_state.get("weather_output")
            if not weather_output:
                raise Exception("No weather output generated")
            
            logger.info(f"Weather retrieval completed [location={location_output.location}] [success={weather_output.api_success}]")
            return weather_output
            
        except Exception as e:
            logger.error(f"Weather retrieval failed [location={location_output.location}] [error={str(e)}]")
            raise Exception(f"Failed to retrieve weather for location {location_output.location}: {str(e)}")
    
    def _validate_location_node(self, state: WeatherAgentState) -> WeatherAgentState:
        """Validate that location information is available."""
        location_output = state["location_output"]
        
        logger.info(f"Validating location for weather retrieval [location={location_output.location}]")
        
        if not location_output.location:
            state["error"] = "No location available for weather retrieval"
            return state
        
        # Check confidence level
        if location_output.confidence < 0.1:
            state["error"] = f"Location confidence too low for weather retrieval: {location_output.confidence}"
            return state
        
        logger.info(f"Location validation passed [location={location_output.location}] [confidence={location_output.confidence}]")
        return state
    
    def _should_fetch_weather(self, state: WeatherAgentState) -> str:
        """Determine whether to proceed with weather fetching."""
        if state.get("error"):
            return "error"
        return "fetch"
    
    def _fetch_weather_node(self, state: WeatherAgentState) -> WeatherAgentState:
        """Fetch weather data from WeatherAPI."""
        location_output = state["location_output"]
        location = location_output.location
        
        logger.info(f"Fetching weather data from API [location={location}]")
        
        try:
            # Check if WeatherAPI is configured
            if not settings.is_weather_api_configured():
                raise Exception("WeatherAPI key not configured. Please set WEATHER_API_KEY environment variable.")
            
            # Prepare API request
            url = settings.get_weather_api_url("current.json")
            params = {
                "key": settings.WEATHER_API_KEY,
                "q": location,
                "aqi": "no"  # We don't need air quality data
            }
            
            # Make API request
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Store raw weather data in state for processing
            state["raw_weather_data"] = weather_data
            logger.info(f"Weather data fetched successfully [location={location}]")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API request failed [location={location}] [error={str(e)}]")
            state["error"] = f"Weather API request failed: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error fetching weather [location={location}] [error={str(e)}]")
            state["error"] = f"Unexpected error fetching weather: {str(e)}"
        
        return state
    
    def _should_process_weather(self, state: WeatherAgentState) -> str:
        """Determine whether to proceed with weather processing."""
        if state.get("error"):
            return "error"
        return "process"
    
    def _process_weather_node(self, state: WeatherAgentState) -> WeatherAgentState:
        """Process raw weather data into structured output."""
        location_output = state["location_output"]
        raw_weather_data = state.get("raw_weather_data")
        
        logger.info(f"Processing weather data [location={location_output.location}]")
        
        try:
            # Extract data directly from the API response
            current_data = raw_weather_data.get("current", {})
            condition_data = current_data.get("condition", {})
            
            # Create weather output directly
            timestamp = datetime.now().isoformat()
            weather_output = WeatherOutput(
                location_used=location_output.location,
                current_temperature_celsius=current_data.get("temp_c"),
                current_temperature_fahrenheit=current_data.get("temp_f"),
                weather_condition=condition_data.get("text"),
                humidity=current_data.get("humidity"),
                wind_speed_kph=current_data.get("wind_kph"),
                api_success=True,
                data_source="WeatherAPI.com",
                timestamp=timestamp
            )
            
            state["weather_output"] = weather_output
            logger.info(f"Weather data processed [location={location_output.location}] [temperature={weather_output.current_temperature_celsius}°C]")
            
        except Exception as e:
            logger.error(f"Weather data processing failed [location={location_output.location}] [error={str(e)}]")
            
            # Create fallback weather output with error information
            timestamp = datetime.now().isoformat()
            fallback_output = WeatherOutput(
                location_used=location_output.location,
                api_success=False,
                api_error=f"Failed to process weather data: {str(e)}",
                data_source="WeatherAPI.com",
                timestamp=timestamp
            )
            state["weather_output"] = fallback_output
        
        return state 