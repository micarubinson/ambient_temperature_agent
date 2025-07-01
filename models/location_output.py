"""
Pydantic model for location agent output.
Defines the structured output format for location extraction from equipment metadata.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class LocationOutput(BaseModel):
    """
    Structured output model for location extraction from equipment metadata.
    
    This model defines the expected output format from the location agent
    that analyzes synthetic metadata to determine equipment location.
    """
    
    location: Optional[str] = Field(
        description="Summarized location of the equipment (e.g., 'New York, NY, USA' or 'Berlin, Germany'). "
                   "Should be None if location cannot be determined."
    )
    
    evidence: str = Field(
        description="Detailed explanation of how the location was determined, including which metadata "
                   "fields were used and the reasoning process. If location is None, explain why."
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level in the location determination (0.0 to 1.0). "
                   "Lower values indicate uncertainty or inference-based decisions."
    )
    
    # Optional detailed location fields
    street: Optional[str] = Field(
        default=None,
        description="Street address if clearly identifiable from metadata"
    )
    
    city: Optional[str] = Field(
        default=None,
        description="City name if clearly identifiable from metadata"
    )
    
    state: Optional[str] = Field(
        default=None,
        description="State/province if clearly identifiable from metadata"
    )
    
    country: Optional[str] = Field(
        default=None,
        description="Country name if clearly identifiable from metadata"
    )
    
    # Conflict detection
    has_location_conflict: bool = Field(
        default=False,
        description="True if conflicting location information was detected in metadata"
    )
    
    conflict_details: Optional[str] = Field(
        default=None,
        description="Details about location conflicts found in metadata"
    )
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    @validator('location')
    def validate_location_consistency(cls, v, values):
        """Ensure location is consistent with confidence level."""
        confidence = values.get('confidence', 0.0)
        if v is None and confidence > 0.5:
            raise ValueError('High confidence requires a location value')
        return v
    
    def is_high_confidence(self) -> bool:
        """Check if the location determination has high confidence."""
        return self.confidence >= 0.7
    
    def is_low_confidence(self) -> bool:
        """Check if the location determination has low confidence."""
        return self.confidence < 0.3
    
    def get_formatted_location(self) -> str:
        """Get a formatted location string for display purposes."""
        if self.location:
            return self.location
        elif any([self.city, self.state, self.country]):
            parts = [part for part in [self.city, self.state, self.country] if part]
            return ", ".join(parts)
        else:
            return "Location unknown"