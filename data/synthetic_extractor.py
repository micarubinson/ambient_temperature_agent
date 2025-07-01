"""
Synthetic data extraction for equipment location metadata.
Uses a JSON-based dataset for comprehensive location information.
"""

import logging
import json
import os
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)


class SyntheticDataExtractor:
    """
    Extracts equipment location metadata from a synthetic JSON dataset.
    
    Provides comprehensive location information including physical location,
    organizational details, and metadata for fictional industrial equipment.
    """
    
    def __init__(self, data_file: str = "equipment_database.json"):
        """Initialize with path to equipment database."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(current_dir, data_file)
        self._load_data()
    
    def _load_data(self):
        """Load equipment data from JSON file."""
        try:
            with open(self.data_file, 'r') as f:
                raw_data = json.load(f)
                
            # Convert array-based structure to ID-based lookup
            if 'equipment_database' in raw_data:
                equipment_list = raw_data['equipment_database']
                self.equipment_data = {}
                for equipment in equipment_list:
                    eq_id = equipment.get('equipment_id')
                    if eq_id:
                        self.equipment_data[eq_id] = equipment
            else:
                # Assume it's already in the correct format
                self.equipment_data = raw_data
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Equipment database not found at {self.data_file}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in equipment database: {self.data_file}")
    
    def extract_equipment_metadata(self, equipment_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract location metadata for a specific equipment from synthetic dataset.
        
        Args:
            equipment_id: Unique identifier for the equipment
            
        Returns:
            Dictionary containing equipment metadata or None if not found
        """
        equipment = self.equipment_data.get(equipment_id)
        if not equipment:
            return None
        
        # Transform data into standardized format compatible with location agent
        metadata = {
            # Equipment identifiers
            'equipment_id': equipment_id,
            'machine_id': equipment_id,  # Legacy compatibility
            'equipment_name': equipment.get('equipment_name', ''),
            'machine_name': equipment.get('equipment_name', ''),  # Legacy compatibility
            'equipment_type': equipment.get('equipment_type', ''),
            'manufacturer': equipment.get('manufacturer', ''),
            'model': equipment.get('model', ''),
            'serial_number': equipment.get('serial_number', ''),
            
            # Physical location information (direct from JSON structure)
            'address_formatted': equipment.get('address_formatted', ''),
            'address_city': equipment.get('address_city', ''),
            'address_state': equipment.get('address_state', ''),
            'address_country': equipment.get('address_country', ''),
            'address_street': equipment.get('address_street', ''),
            'address_street_number': equipment.get('address_street_number', ''),
            'address_zip_code': equipment.get('address_zip_code', ''),
            'location_lat': equipment.get('location_lat'),
            'location_lng': equipment.get('location_lng'),
            
            # Organizational location information (direct from JSON structure)
            'building_name': equipment.get('building_name', ''),
            'building_id': equipment.get('building_id', ''),
            'facility_name': equipment.get('facility_name', ''),
            'branch_name': equipment.get('branch_name', ''),
            'region_name': equipment.get('region_name', ''),
            'company_name': equipment.get('company_name', ''),
            'building_parent_name': equipment.get('building_parent_name', ''),
            'country_name_by_location': equipment.get('country_name_by_location', ''),
            
            # Additional metadata
            'installation_date': equipment.get('installation_date', ''),
            'operational_status': equipment.get('operational_status', 'unknown'),
            'power_rating': equipment.get('power_rating', ''),
            'operating_temperature_range': equipment.get('operating_temperature_range', ''),
            'last_maintenance': equipment.get('last_maintenance', ''),
            'notes': equipment.get('notes', ''),
            'metadata_tags': equipment.get('metadata_tags', [])
        }
        
        return metadata
    
    def list_all_equipment(self) -> list:
        """Get list of all available equipment IDs."""
        return list(self.equipment_data.keys())
    
    def get_equipment_count(self) -> int:
        """Get total number of equipment in database."""
        return len(self.equipment_data)
    
    def search_by_type(self, equipment_type: str) -> Dict[str, Dict]:
        """Find all equipment of a specific type."""
        return {
            eq_id: eq_data 
            for eq_id, eq_data in self.equipment_data.items() 
            if eq_data.get('equipment_type', '').lower() == equipment_type.lower()
        }
    
    def search_by_location(self, city: str = None, country: str = None) -> Dict[str, Dict]:
        """Find equipment by physical location."""
        results = {}
        for eq_id, eq_data in self.equipment_data.items():
            
            # Check city match
            city_match = True
            if city:
                eq_city = eq_data.get('address_city', '').lower()
                city_match = city.lower() in eq_city
            
            # Check country match  
            country_match = True
            if country:
                eq_country = eq_data.get('address_country', '').lower()
                country_match = country.lower() in eq_country
            
            if city_match and country_match:
                results[eq_id] = eq_data
                
        return results


# Legacy function support for backward compatibility
_extractor_instance = None

def extract_equipment_metadata(equipment_id: str) -> Dict[str, Any]:
    """
    Legacy function wrapper for equipment metadata extraction.
    
    Args:
        equipment_id: The equipment ID to query for
        
    Returns:
        Dictionary containing equipment location metadata, or empty dict if no data found
    """
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = SyntheticDataExtractor()
    
    result = _extractor_instance.extract_equipment_metadata(equipment_id)
    return result if result is not None else {}


def get_location_summary(metadata: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of available location information.
    
    Args:
        metadata: Dictionary containing equipment metadata
        
    Returns:
        String summary of location information
    """
    if not metadata:
        return "No metadata available"
    
    location_fields = [
        'address_formatted', 'address_city', 'address_state', 'address_country',
        'building_name', 'facility_name', 'branch_name', 'region_name', 'company_name'
    ]
    
    available_info = []
    for field in location_fields:
        value = metadata.get(field)
        if value and str(value).strip():
            available_info.append(f"{field}: {value}")
    
    if not available_info:
        return "No location information available in metadata"
    
    return "; ".join(available_info)


def list_available_equipment() -> list:
    """
    List all available equipment IDs in the database.
    
    Returns:
        List of equipment IDs
    """
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = SyntheticDataExtractor()
    
    return _extractor_instance.list_all_equipment()


def get_equipment_info(equipment_id: str) -> str:
    """
    Get a brief description of equipment for help/documentation.
    
    Args:
        equipment_id: The equipment ID
        
    Returns:
        String description of the equipment
    """
    try:
        metadata = extract_equipment_metadata(equipment_id)
        if not metadata:
            return f"{equipment_id}: Equipment not found"
        
        name = metadata.get('machine_name', metadata.get('equipment_name', 'Unknown Equipment'))
        eq_type = metadata.get('equipment_type', 'Unknown Type')
        location = metadata.get('address_city', metadata.get('facility_name', 'Unknown Location'))
        
        return f"{equipment_id}: {name} ({eq_type}) - {location}"
        
    except Exception as e:
        return f"{equipment_id}: Error loading equipment info - {str(e)}"


