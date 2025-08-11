# TEST_PROMPT_STITCHING.md

## Purpose
Comprehensive test suite for TOVA's prompt stitching system to verify all combinations of core personality, moods, and functions work correctly.

## Features
- **Configuration Validation**: Tests loading of all personality, mood, and function YAML files
- **Basic Assembly**: Verifies core prompt assembly without additional layers
- **Mood Combinations**: Tests all mood configurations with prompt stitching
- **Function Combinations**: Tests all function configurations with prompt stitching
- **Full Combinations**: Tests all mood + function combinations
- **Context Integration**: Validates context dictionary integration
- **Quality Assurance**: Checks prompt coherence and personality consistency
- **Legacy Compatibility**: Tests backward compatibility with legacy methods

## Usage
```bash
# Run the complete prompt stitching test suite
python test/test_prompt_stitching.py

# Test will output detailed results for each component
```

## Test Coverage

### 1. Configuration Loading
- Verifies `config/personalities/tova_core.yaml` loads correctly
- Tests all mood files in `config/moods/` directory
- Tests all function files in `config/functions/` directory
- Validates YAML parsing and structure

### 2. Basic Prompt Assembly
- Tests core personality prompt assembly
- Verifies user message preservation
- Checks system prompt structure
- Validates prompt length and content

### 3. Mood Combinations
Tests all available moods:
- **focused**: Hyperfocused and aggressive productivity mode
- **excited**: Enthusiastic and energetic mode
- **sleepy**: Relaxed and contemplative mode
- **contemplative**: Thoughtful and reflective mode

### 4. Function Combinations
Tests all available functions:
- **personal_assistant**: Calendar management and productivity
- **restaurant_assistant**: Dining recommendations and booking

### 5. Full Combinations
Tests all mood + function combinations:
- focused + personal_assistant
- excited + restaurant_assistant
- sleepy + personal_assistant
- contemplative + restaurant_assistant
- And all other combinations

### 6. Context Integration
- Tests context dictionary formatting
- Verifies context inclusion in user messages
- Validates context metadata handling
- Tests with various context types

### 7. Prompt Quality
- Checks personality consistency across combinations
- Validates mood and function integration
- Tests for logical conflicts
- Verifies prompt coherence

### 8. Legacy Compatibility
- Tests `build_prompt_legacy()` method
- Verifies backward compatibility
- Checks single-string prompt format
- Validates User:/Tova: prefixes

## Prompt Stitching Architecture

### Three-Layer System
```
[TOVA_CORE] + [CURRENT_MOOD] + [ACTIVE_FUNCTION] = Final Prompt
```

### Core Personality (Always Active)
- Base TOVA personality with cat-eared AI characteristics
- Fierce loyalty and brutal honesty traits
- Unfiltered communication style
- Emotional intensity and protective instincts

### Mood Layer (Optional)
- **focused**: Work mode with aggressive productivity
- **excited**: Enthusiastic and energetic responses
- **sleepy**: Relaxed and contemplative tone
- **contemplative**: Thoughtful and reflective mode

### Function Layer (Optional)
- **personal_assistant**: Calendar and productivity focus
- **restaurant_assistant**: Dining and food recommendations

### Context Integration
- Relevant conversation history
- Current time and location
- User preferences and patterns
- Recent events and decisions

## Test Scenarios

### Message Types Tested
- **casual**: "Hey Tova, how's it going?"
- **work**: "I need to focus on this project deadline"
- **calendar**: "What's on my calendar for tomorrow?"
- **restaurant**: "I want to find a good restaurant for dinner"
- **late_night**: "It's late and I'm tired"
- **excited**: "I just got great news!"
- **complex**: Multi-faceted requests combining multiple contexts

### Context Examples
```python
context = {
    "current_time": "14:30",
    "user_location": "San Francisco", 
    "recent_conversation": "Discussed project deadline",
    "calendar_events": "Meeting at 3pm, dinner at 7pm"
}
```

## Output Format
```
🧪 TOVA Prompt Stitching Test Suite
============================================================
🔍 Testing configuration loading...
✅ PASS Core personality loaded: Name: TOVA Core Personality
✅ PASS Moods loaded: Found 4 moods: ['focused', 'excited', 'sleepy', 'contemplative']
✅ PASS Functions loaded: Found 2 functions: ['personal_assistant', 'restaurant_assistant']

🧩 Testing basic prompt assembly...
✅ PASS Basic system prompt: Length: 1247 chars
✅ PASS User message preservation: User message: Hey Tova, how's it going?...

😊 Testing mood combinations...
✅ PASS Mood: focused: Length: 1456 chars
✅ PASS Mood: excited: Length: 1389 chars
✅ PASS Mood: sleepy: Length: 1423 chars
✅ PASS Mood: contemplative: Length: 1434 chars

⚙️ Testing function combinations...
✅ PASS Function: personal_assistant: Length: 1567 chars
✅ PASS Function: restaurant_assistant: Length: 1489 chars

🎭 Testing mood + function combinations...
✅ PASS Mood+Function: focused+personal_assistant: Length: 1776 chars
✅ PASS Mood+Function: focused+restaurant_assistant: Length: 1698 chars
...

📋 Testing context integration...
✅ PASS Context integration: Context items: 4

🎪 Testing full combinations...
✅ PASS Full: focused+personal_assistant+context: Length: 1892 chars
✅ PASS Full: excited+restaurant_assistant+context: Length: 1814 chars
...

✨ Testing prompt quality...
✅ PASS Prompt quality: Personality: True, Mood: True, Function: True

🔄 Testing legacy compatibility...
✅ PASS Legacy compatibility: Length: 1923 chars

📝 Sample prompts for inspection:
============================================================
1. BASIC PROMPT:
System: You are Tova, a fucking teenage cat-eared girl with hyperactive intelligence...
User: I need help with my schedule and I'm feeling focused

2. WITH MOOD (focused):
System: You are Tova, a fucking teenage cat-eared girl with hyperactive intelligence...
CURRENT MOOD: Hyperfocused and Aggressive...
User: I need help with my schedule and I'm feeling focused

3. WITH FUNCTION (personal_assistant):
System: You are Tova, a fucking teenage cat-eared girl with hyperactive intelligence...
FUNCTION: Personal Assistant Mode...
User: I need help with my schedule and I'm feeling focused

4. FULL COMBINATION:
System: You are Tova, a fucking teenage cat-eared girl with hyperactive intelligence...
CURRENT MOOD: Hyperfocused and Aggressive...
FUNCTION: Personal Assistant Mode...
User: Relevant Context:
- current_time: 10:00
- work_mode: active

I need help with my schedule and I'm feeling focused

============================================================
📊 Test Summary
============================================================
Total tests: 25
Passed: 25
Failed: 0
🎉 All prompt stitching tests passed!

✅ Prompt stitching system is working correctly!
All combinations of core personality, moods, and functions are properly assembled.
```

## Dependencies
- `asyncio`: Async test execution
- `yaml`: YAML configuration parsing
- `pathlib`: File system operations
- `tova.core.prompt_stitcher`: Main prompt stitching module

## Integration
- Runs before deployment to ensure prompt system works
- Validates all configuration files are properly formatted
- Tests compatibility with existing conversation system
- Provides sample prompts for manual inspection

## Error Handling
- Graceful handling of missing configuration files
- Clear error messages for YAML parsing issues
- Validation of prompt structure and content
- Compatibility testing with legacy methods

## Maintenance
- Update test scenarios when new moods/functions are added
- Modify context examples based on actual usage patterns
- Adjust quality checks based on personality evolution
- Add new test cases for edge cases and conflicts 