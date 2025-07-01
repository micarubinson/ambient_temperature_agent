"""
Location LLM Agent using LangGraph for structured location extraction.
Analyzes synthetic metadata to determine equipment location with confidence scoring.
"""

import logging
from typing import Dict, Any, Optional, TypedDict
import json

# LangGraph imports
from langgraph.graph import StateGraph, END

# LangChain imports
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Project imports
from config.settings import settings
from models.location_output import LocationOutput

# Configure logging
logger = logging.getLogger(__name__)


class LocationAgentState(TypedDict):
    """State object for the location agent graph."""
    equipment_id: str
    metadata: Dict[str, Any]
    location_output: Optional[LocationOutput]
    error: Optional[str]


class LocationAgent:
    """
    LangGraph-based agent for extracting location information from equipment metadata.
    
    Uses a graph structure to process metadata and extract structured location
    information with confidence scoring and evidence tracking.
    """
    
    def __init__(self):
        """Initialize the location agent with LLM and graph setup."""
        self.llm = self._setup_llm()
        self.output_parser = PydanticOutputParser(pydantic_object=LocationOutput)
        self.graph = self._build_graph()
        logger.info("LocationAgent initialized [temperature=0.0]")
    
    def _setup_llm(self):
        """Setup LLM (Azure OpenAI or OpenAI) with zero temperature."""
        if settings.is_azure_openai_configured():
            logger.info("Using Azure OpenAI for location agent")
            return AzureChatOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                deployment_name=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                temperature=settings.LOCATION_AGENT_TEMPERATURE
            )
        elif settings.is_openai_configured():
            logger.info("Using OpenAI for location agent")
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_MODEL,
                temperature=settings.LOCATION_AGENT_TEMPERATURE
            )
        else:
            raise Exception("No LLM configuration found. Please set OPENAI_API_KEY or Azure OpenAI credentials.")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for location extraction."""
        graph = StateGraph(LocationAgentState)
        
        # Add nodes
        graph.add_node("validate_metadata", self._validate_metadata_node)
        graph.add_node("extract_location", self._extract_location_node)
        graph.add_node("infer_location", self._infer_location_node)
        
        # Add edges
        graph.set_entry_point("validate_metadata")
        graph.add_conditional_edges(
            "validate_metadata",
            self._should_extract_or_infer,
            {
                "extract": "extract_location",
                "infer": "infer_location",
                "error": END
            }
        )
        graph.add_edge("extract_location", END)
        graph.add_edge("infer_location", END)
        
        return graph.compile()
    
    def analyze_location(self, equipment_id: str, metadata: Dict[str, Any]) -> LocationOutput:
        """
        Analyze metadata to extract location information.
        
        Args:
            equipment_id: The equipment ID being analyzed
            metadata: Dictionary containing equipment metadata from synthetic dataset
            
        Returns:
            LocationOutput with structured location information
            
        Raises:
            Exception: If location analysis fails
        """
        logger.info(f"Starting location analysis [equipment_id={equipment_id}]")
        
        # Initialize state
        initial_state = LocationAgentState(
            equipment_id=equipment_id,
            metadata=metadata,
            location_output=None,
            error=None
        )
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            if final_state.get("error"):
                raise Exception(final_state["error"])
            
            location_output = final_state.get("location_output")
            if not location_output:
                raise Exception("No location output generated")
            
            logger.info(f"Location analysis completed [equipment_id={equipment_id}] [confidence={location_output.confidence}]")
            return location_output
            
        except Exception as e:
            logger.error(f"Location analysis failed [equipment_id={equipment_id}] [error={str(e)}]")
            raise Exception(f"Failed to analyze location for equipment {equipment_id}: {str(e)}")
    
    def _validate_metadata_node(self, state: LocationAgentState) -> LocationAgentState:
        """Validate that metadata contains usable information."""
        equipment_id = state["equipment_id"]
        metadata = state["metadata"]
        
        logger.info(f"Validating metadata [equipment_id={equipment_id}]")
        
        if not metadata:
            state["error"] = "No metadata provided"
            return state
        
        # Check for any location-related fields
        location_fields = [
            'address_formatted', 'address_city', 'address_state', 'address_country',
            'building_name', 'facility_name', 'branch_name', 'region_name', 'company_name'
        ]
        
        available_fields = [field for field in location_fields if metadata.get(field)]
        logger.info(f"Available location fields [equipment_id={equipment_id}] [count={len(available_fields)}]")
        
        if not available_fields:
            state["error"] = "No location information available in metadata"
            return state
        
        return state
    
    def _should_extract_or_infer(self, state: LocationAgentState) -> str:
        """Determine whether to extract directly or infer location."""
        if state.get("error"):
            return "error"
        
        metadata = state["metadata"]
        
        # Check if we have direct address information
        direct_fields = ['address_formatted', 'address_city', 'address_state', 'address_country']
        has_direct_info = any(metadata.get(field) for field in direct_fields)
        
        if has_direct_info:
            logger.info(f"Direct location information available [equipment_id={state['equipment_id']}]")
            return "extract"
        else:
            logger.info(f"No direct location info, will infer [equipment_id={state['equipment_id']}]")
            return "infer"
    
    def _detect_location_conflicts(self, metadata: Dict[str, Any], equipment_id: str) -> tuple[bool, Optional[str]]:
        """
        Detect conflicts between physical and organizational location indicators.
        
        Args:
            metadata: Equipment metadata dictionary
            equipment_id: Equipment ID for logging
            
        Returns:
            Tuple of (has_conflict, conflict_details)
        """
        # Physical location indicators
        physical_indicators = {
            'address_formatted': metadata.get('address_formatted'),
            'address_city': metadata.get('address_city'),
            'address_state': metadata.get('address_state'),
            'address_country': metadata.get('address_country')
        }
        
        # Organizational location indicators  
        org_indicators = {
            'facility_name': metadata.get('facility_name'),
            'building_parent_name': metadata.get('building_parent_name'),
            'branch_name': metadata.get('branch_name'),
            'region_name': metadata.get('region_name')
        }
        
        # Extract location components from available data
        conflicts = []
        
        # Check for city conflicts
        physical_city = physical_indicators.get('address_city')
        if physical_city:
            # Check if facility_name contains a different city
            facility_name = org_indicators.get('facility_name', '')
            if facility_name and ',' in facility_name:
                # Extract city from "City, State" format
                facility_parts = facility_name.split(',')
                if len(facility_parts) >= 2:
                    facility_city = facility_parts[0].strip()
                    if facility_city.lower() != physical_city.lower():
                        conflicts.append(f"Physical city '{physical_city}' vs facility city '{facility_city}'")
        
        # Check for state conflicts in facility_name
        physical_state = physical_indicators.get('address_state')
        facility_name = org_indicators.get('facility_name', '')
        if physical_state and facility_name and ',' in facility_name:
            facility_parts = facility_name.split(',')
            if len(facility_parts) >= 2:
                facility_state = facility_parts[1].strip()
                if facility_state.lower() != physical_state.lower():
                    conflicts.append(f"Physical state '{physical_state}' vs facility state '{facility_state}'")
        
        # Check for general location mismatches in formatted address vs facility
        address_formatted = physical_indicators.get('address_formatted', '')
        if address_formatted and facility_name:
            # Simple check: if facility mentions a city/state not in the formatted address
            if facility_name and ',' in facility_name:
                facility_location = facility_name.split(',')[0].strip()
                if facility_location and facility_location.lower() not in address_formatted.lower():
                    # Only flag if it's a significant difference (not just abbreviations)
                    if len(facility_location) > 3:  # Avoid flagging abbreviations
                        conflicts.append(f"Address location vs facility location: '{facility_location}' not found in address")
        
        has_conflict = len(conflicts) > 0
        conflict_details = "; ".join(conflicts) if conflicts else None
        
        if has_conflict:
            logger.warning(f"Location conflict detected [equipment_id={equipment_id}] [conflicts={conflict_details}]")
        
        return has_conflict, conflict_details
    
    def _extract_location_node(self, state: LocationAgentState) -> LocationAgentState:
        """Extract location from direct metadata fields."""
        equipment_id = state["equipment_id"]
        metadata = state["metadata"]
        
        logger.info(f"Extracting location from direct metadata [equipment_id={equipment_id}]")
        
        prompt = ChatPromptTemplate.from_template("""
You are a location extraction expert. Analyze the following industrial equipment metadata and extract the location information.

Equipment ID: {equipment_id}
Metadata: {metadata}

Extract the location information with high confidence since direct address data is available.
Focus on the address fields, building information, and geographic data.

{format_instructions}
""")
        
        try:
            # Detect location conflicts before processing
            has_conflict, conflict_details = self._detect_location_conflicts(metadata, equipment_id)
            
            chain = prompt | self.llm | self.output_parser
            
            location_output = chain.invoke({
                "equipment_id": equipment_id,
                "metadata": json.dumps(metadata, indent=2),
                "format_instructions": self.output_parser.get_format_instructions()
            })
            
            # Add conflict information to the output
            location_output.has_location_conflict = has_conflict
            location_output.conflict_details = conflict_details
            
            state["location_output"] = location_output
            logger.info(f"Location extracted [equipment_id={equipment_id}] [confidence={location_output.confidence}] [has_conflict={has_conflict}]")
            
        except Exception as e:
            logger.error(f"Location extraction failed [equipment_id={equipment_id}] [error={str(e)}]")
            state["error"] = f"Location extraction failed: {str(e)}"
        
        return state
    
    def _infer_location_node(self, state: LocationAgentState) -> LocationAgentState:
        """Infer location from indirect metadata (company, facility, etc.)."""
        equipment_id = state["equipment_id"]
        metadata = state["metadata"]
        
        logger.info(f"Inferring location from indirect metadata [equipment_id={equipment_id}]")
        
        prompt = ChatPromptTemplate.from_template("""
You are a location inference expert. The industrial equipment metadata lacks direct address information, 
but contains company, facility, and organizational data that may help infer the location.

Equipment ID: {equipment_id}
Metadata: {metadata}

Try to infer the equipment location based on:
- Company name and known company locations
- Facility/branch names that might indicate geographic areas
- Building or organizational hierarchy information

IMPORTANT: 
- Use lower confidence scores (0.1-0.5) since this is inference, not direct data
- Clearly state in the evidence that this is inferred, not from direct metadata
- If you cannot make a reasonable inference, set location to null and explain why

{format_instructions}
""")
        
        try:
            # Detect location conflicts before processing
            has_conflict, conflict_details = self._detect_location_conflicts(metadata, equipment_id)
            
            chain = prompt | self.llm | self.output_parser
            
            location_output = chain.invoke({
                "equipment_id": equipment_id,
                "metadata": json.dumps(metadata, indent=2),
                "format_instructions": self.output_parser.get_format_instructions()
            })
            
            # Add conflict information to the output
            location_output.has_location_conflict = has_conflict
            location_output.conflict_details = conflict_details
            
            state["location_output"] = location_output
            logger.info(f"Location inferred [equipment_id={equipment_id}] [confidence={location_output.confidence}] [has_conflict={has_conflict}]")
            
        except Exception as e:
            logger.error(f"Location inference failed [equipment_id={equipment_id}] [error={str(e)}]")
            state["error"] = f"Location inference failed: {str(e)}"
        
        return state 