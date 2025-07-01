# Ambient Temperature Agent

A standalone industrial equipment temperature analysis system that takes an equipment ID, analyzes location metadata using LLM, and retrieves ambient temperature data. Built with LangGraph and LangChain for robust, graph-based workflow orchestration.

## Overview

The Ambient Temperature Agent follows this flow:
1. **Input**: Equipment ID (e.g., `PUMP_001_NYC`)
2. **Synthetic Data Extraction**: Retrieves equipment and building metadata from JSON dataset
3. **Location Analysis**: Uses LLM to determine equipment location with confidence scoring
4. **Weather Retrieval**: Gets current temperature data from WeatherAPI
5. **Output**: Formatted response with temperature information

## Features

- **Graph-Based Workflow**: Uses LangGraph for robust state management
- **Location Conflict Detection**: Identifies discrepancies between physical and organizational location data
- **Confidence Scoring**: Provides confidence levels for location determinations
- **Error Handling**: Comprehensive error handling with fallback responses
- **Zero Temperature LLMs**: Prevents hallucinations in location and weather processing
- **Synthetic Dataset**: Uses fictional industrial equipment data to avoid proprietary information
- **Flexible LLM Support**: Works with OpenAI or Azure OpenAI

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

#### Option A: Environment Variables (Recommended)

Add these lines to your `~/.zshrc` file:

```bash
# Ambient Temperature Agent API Keys
export WEATHER_API_KEY="your_weather_api_key_here"
export OPENAI_API_KEY="your_openai_api_key_here"
```

Then reload your shell:
```bash
source ~/.zshrc
```

#### Option B: .env File

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 3. Get API Keys

#### WeatherAPI (Required)
1. Sign up at [WeatherAPI.com](https://www.weatherapi.com/)
2. Get your free API key
3. Set it as `WEATHER_API_KEY`

#### OpenAI (Required - Choose One)

**Option 1: Standard OpenAI**
1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Set `OPENAI_API_KEY`

**Option 2: Azure OpenAI**
1. Set up Azure OpenAI resource
2. Configure these variables:
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_DEPLOYMENT_NAME`
   - `AZURE_OPENAI_API_VERSION`

## Usage

### Command Line Interface

```bash
# Analyze specific equipment
python ambient_temp_agent.py <equipment_id>

# List available equipment
python ambient_temp_agent.py --list

# Show help
python ambient_temp_agent.py --help
```

### Examples

```bash
# High-confidence case with complete address
python ambient_temp_agent.py PUMP_001_NYC

# Location conflict scenario
python ambient_temp_agent.py COMP_002_CONFLICT

# Inference-only case (missing address data)
python ambient_temp_agent.py MOTOR_003_MINIMAL

# International equipment
python ambient_temp_agent.py GEN_004_INTL_DE
```

### Programmatic Usage

```python
from ambient_temp_agent import AmbientTempAgent

agent = AmbientTempAgent()
result = agent.get_ambient_temperature("PUMP_001_NYC")
print(result.formatted_response)
```

## Available Equipment

The system includes 15 fictional industrial equipment items showcasing different scenarios:

### High-Confidence Cases (Complete Address Data)
- **PUMP_001_NYC**: Centrifugal Pump in New York City
- **GEN_004_INTL_DE**: Backup Generator in Munich, Germany
- **PUMP_006_UK**: Water Circulation Pump in Manchester, UK
- **TURB_008_FR**: Steam Turbine in Lyon, France
- **BOILER_010_JP**: Industrial Boiler in Tokyo, Japan
- **CRUSHER_012_CA**: Rock Crusher in Calgary, Canada
- **PRESS_014_AU**: Hydraulic Press in Sydney, Australia

### Location Conflict Cases (Demonstrates Conflict Detection)
- **COMP_002_CONFLICT**: Physical address in Grafton, WI vs facility in Milwaukee, WI
- **HVAC_005_CONFLICT_CA**: Physical address in San Diego, CA vs facility in Los Angeles, CA
- **COMP_009_MAJOR_CONFLICT**: Physical address in Houston, TX vs facility in Dallas, TX
- **DRILL_015_CONFLICT_INTL**: Physical address in Milan, Italy vs facility in Rome, Italy

### Inference Cases (Missing Address, Organization-Based)
- **MOTOR_003_MINIMAL**: Only company and facility information available
- **CONV_007_SPARSE**: Limited data requiring inference
- **FAN_011_INCOMPLETE**: Partial location information
- **MIXER_013_VAGUE**: Very minimal data, challenging case

## Location Conflict Detection

### Why Conflicts Matter

Industrial equipment location conflicts occur when:
- **Physical Location**: Where the equipment is actually installed
- **Organizational Location**: Where the company/facility is registered or managed

These conflicts are critical for accurate temperature analysis because they affect:
- Weather data accuracy
- Maintenance scheduling
- Regulatory compliance
- Emergency response planning

### Conflict Examples

**COMP_002_CONFLICT** demonstrates a typical scenario:
- **Physical Address**: `975 Port Washington Road, Grafton, WI 53024, USA`
- **Facility Name**: `Milwaukee Operations Hub`
- **Conflict**: Equipment physically located in Grafton but managed by Milwaukee facility

**Expected Output**:
```
Location Conflicts: Yes
[WARNING] Location conflict detected [equipment_id=COMP_002_CONFLICT] 
[conflicts=Physical city 'Grafton' vs facility city 'Milwaukee']
```

The system correctly identifies Grafton as the physical location (higher confidence) while flagging the organizational conflict.

## Output Format

### Success Response
```
"Industrial equipment PUMP_001_NYC is located in New York, NY, USA and the temperature in this location is 12.2°C"
```

### Detailed Results
```
================================================================================
AMBIENT TEMPERATURE AGENT RESULTS
================================================================================
Equipment ID: PUMP_001_NYC
Location: New York, NY, USA
Location Confidence: 1.00
Location Conflicts: No
Weather API Success: Yes
Temperature: 12.2°C (54.0°F)
Weather Condition: Partly cloudy

Formatted Response:
"Industrial equipment PUMP_001_NYC is located in New York, NY, USA and the temperature in this location is 12.2°C"
================================================================================
```

## Location Analysis

### Direct Extraction vs Inference

The location agent uses two paths:

1. **Direct Extraction** (High Confidence: 0.7-1.0):
   - Uses address fields: `address_formatted`, `address_city`, `address_state`
   - Example: "1250 Broadway, New York, NY 10001, USA" → "New York, NY, USA"

2. **Inference** (Lower Confidence: 0.1-0.5):
   - Uses organizational data: `facility_name`, `company_name`, `branch_name`
   - Example: "Pittsburgh Steel Plant" → "Pittsburgh, PA, USA"

### Confidence Scoring
- **0.7-1.0**: High confidence (direct address data)
- **0.3-0.7**: Medium confidence (partial address or strong organizational indicators)
- **0.1-0.3**: Low confidence (inference from limited organizational data)
- **0.0**: No location determinable

## Error Handling

### Common Error Scenarios

1. **Missing API Keys**:
   ```
   ERROR: Missing required configuration: WEATHER_API_KEY
   ```

2. **Equipment Not Found**:
   ```
   "Industrial equipment INVALID_ID could not be processed: No metadata found for equipment"
   ```

3. **Location Determination Failed**:
   ```
   "Industrial equipment MIXER_013_VAGUE could not be processed: Could not determine equipment location"
   ```

4. **Weather API Failure**:
   ```
   "Industrial equipment PUMP_001_NYC is located in New York, NY, USA but the temperature in this location is unavailable"
   ```

## Development

### Project Structure

```
ambient-temp-agent/
├── config/
│   └── settings.py              # Environment-based configuration
├── models/
│   ├── __init__.py
│   ├── location_output.py       # Location analysis output model  
│   ├── weather_output.py        # Weather data output model
│   └── final_response.py        # Final formatted response model
├── data/
│   ├── __init__.py
│   ├── equipment_database.json  # Synthetic equipment dataset
│   └── synthetic_extractor.py   # Data extraction logic
├── agents/
│   ├── __init__.py
│   ├── location_agent.py        # LLM location analysis agent
│   └── weather_agent.py         # Weather data retrieval agent
├── ambient_temp_agent.py        # Main orchestrator
├── test_basic.py               # Basic validation tests
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

### Testing

Test with different equipment types:

```bash
# Test high-confidence case
python ambient_temp_agent.py PUMP_001_NYC

# Test conflict detection
python ambient_temp_agent.py COMP_002_CONFLICT

# Test inference case
python ambient_temp_agent.py MOTOR_003_MINIMAL

# Test international case
python ambient_temp_agent.py GEN_004_INTL_DE
```

### Extending the System

To add new equipment:

1. Edit `data/equipment_database.json`
2. Add new equipment following the existing schema
3. Include various conflict scenarios for testing

To add new data sources:
1. Create new extractor in `data/` directory
2. Update the main orchestrator to use the new extractor

## Configuration Validation

The system validates configuration on startup:

```bash
python ambient_temp_agent.py PUMP_001_NYC
# If missing config:
ERROR: Missing required configuration: WEATHER_API_KEY
```

Validation checks:
- ✅ WeatherAPI key is set and not a placeholder
- ✅ Either OpenAI API key or Azure OpenAI credentials are configured
- ✅ All required environment variables are present

## Troubleshooting

### Common Issues

1. **"No LLM configuration found"**
   - Ensure either `OPENAI_API_KEY` or Azure OpenAI variables are set
   - Check that API keys are not the placeholder values

2. **"WeatherAPI key not configured"**
   - Set `WEATHER_API_KEY` in your environment
   - Verify the key is valid at WeatherAPI.com

3. **"Equipment not found"**
   - Use `python ambient_temp_agent.py --list` to see available equipment
   - Check spelling of equipment ID

4. **Rate limiting errors**
   - WeatherAPI free tier: 1M calls/month
   - OpenAI API: Depends on your plan and usage

### Environment Variables Check

```bash
# Check if variables are set
echo $WEATHER_API_KEY
echo $OPENAI_API_KEY

# If empty, add to ~/.zshrc and reload
source ~/.zshrc
```

## License

This project is designed for personal and educational use. It contains no proprietary information and uses only fictional data.

## 🚀 Contributing

This is a research project, but feel free to fork and modify for your own use cases. The synthetic dataset and LangGraph architecture make it easy to extend with new equipment types and data sources. 

