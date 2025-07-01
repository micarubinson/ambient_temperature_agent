#!/usr/bin/env python3
"""
Basic test for the ambient temperature agent.
Tests synthetic data extraction and location analysis without requiring API keys.
"""

import sys
import os
import json

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.synthetic_extractor import extract_equipment_metadata, list_available_equipment, get_equipment_info
from models.location_output import LocationOutput


def test_synthetic_data_extraction():
    """Test that synthetic data extraction works correctly."""
    print("Testing synthetic data extraction...")
    
    # Test extracting a known equipment
    metadata = extract_equipment_metadata("PUMP_001_NYC")
    assert metadata is not None, "Should extract metadata for PUMP_001_NYC"
    assert metadata.get('machine_id') == 'PUMP_001_NYC', "Machine ID should match"
    assert metadata.get('address_city') == 'New York', "Should have correct city"
    print("✅ Basic metadata extraction works")
    
    # Test extracting non-existent equipment
    empty_metadata = extract_equipment_metadata("NONEXISTENT_EQUIPMENT")
    assert empty_metadata == {}, "Should return empty dict for non-existent equipment"
    print("✅ Non-existent equipment handling works")
    
    # Test listing equipment
    equipment_list = list_available_equipment()
    assert len(equipment_list) > 0, "Should have equipment in database"
    assert "PUMP_001_NYC" in equipment_list, "Should include PUMP_001_NYC"
    print(f"✅ Equipment list works ({len(equipment_list)} items)")
    
    # Test equipment info
    info = get_equipment_info("PUMP_001_NYC")
    assert "PUMP_001_NYC" in info, "Info should contain equipment ID"
    assert "Centrifugal Pump" in info, "Info should contain equipment name"
    print("✅ Equipment info works")


def test_location_model():
    """Test that location output model works correctly."""
    print("\nTesting location model...")
    
    # Test valid location output
    location = LocationOutput(
        location="New York, NY, USA",
        evidence="Based on address_formatted field",
        confidence=0.95,
        city="New York",
        state="NY",
        country="USA",
        has_location_conflict=False
    )
    
    assert location.is_high_confidence(), "Should be high confidence"
    assert not location.is_low_confidence(), "Should not be low confidence"
    assert location.get_formatted_location() == "New York, NY, USA", "Should format correctly"
    print("✅ Location model validation works")


def test_equipment_scenarios():
    """Test different equipment scenarios."""
    print("\nTesting equipment scenarios...")
    
    scenarios = [
        ("PUMP_001_NYC", "High confidence with complete address"),
        ("COMP_002_CONFLICT", "Location conflict scenario"),
        ("MOTOR_003_MINIMAL", "Minimal data inference case"),
        ("GEN_004_INTL_DE", "International equipment"),
        ("MIXER_013_VAGUE", "Very limited data case")
    ]
    
    for equipment_id, description in scenarios:
        metadata = extract_equipment_metadata(equipment_id)
        assert metadata is not None, f"Should have metadata for {equipment_id}"
        print(f"✅ {equipment_id}: {description}")


def test_configuration_placeholders():
    """Test that configuration has proper placeholders."""
    print("\nTesting configuration...")
    
    from config.settings import settings
    
    # These should be placeholders, not real keys
    assert settings.WEATHER_API_KEY == "YOUR_WEATHER_API_KEY_HERE", "Should have placeholder weather key"
    assert settings.OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE", "Should have placeholder OpenAI key"
    
    # Test validation (should fail with placeholders)
    missing = settings.validate_configuration()
    assert len(missing) > 0, "Should detect missing configuration"
    print(f"✅ Configuration validation works (detected {len(missing)} missing items)")


def main():
    """Run all tests."""
    print("Running basic tests for Ambient Temperature Agent")
    print("=" * 80)
    
    try:
        test_synthetic_data_extraction()
        test_location_model()
        test_equipment_scenarios()
        test_configuration_placeholders()
        
        print("\n" + "=" * 80)
        print("🎉 All basic tests passed!")
        print("\nNext steps:")
        print("1. Set up your API keys (WEATHER_API_KEY and OPENAI_API_KEY)")
        print("2. Try: python ambient_temp_agent.py PUMP_001_NYC")
        print("3. List equipment: python ambient_temp_agent.py --list")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 