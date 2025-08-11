#!/usr/bin/env python3
"""Test script for TOVA prompt stitching with all combinations"""

import asyncio
import sys
import os
from pathlib import Path
import yaml
from typing import Dict, List, Tuple

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from tova.core.prompt_stitcher import PromptStitcher

class PromptStitchingTester:
    def __init__(self):
        self.project_root = Path("/home/anthon/t0v4")
        self.config_path = self.project_root / "config"
        self.stitcher = PromptStitcher(str(self.config_path))
        
        # Test messages for different scenarios
        self.test_messages = {
            "casual": "Hey Tova, how's it going?",
            "work": "I need to focus on this project deadline",
            "calendar": "What's on my calendar for tomorrow?",
            "restaurant": "I want to find a good restaurant for dinner",
            "late_night": "It's late and I'm tired",
            "excited": "I just got great news!",
            "complex": "I need help with my schedule, finding a restaurant, and I'm feeling pretty focused right now"
        }
        
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if details:
            result += f": {details}"
        print(result)
        self.test_results.append((test_name, success, details))
    
    def test_config_loading(self):
        """Test 1: Verify all configuration files load correctly"""
        print("\n🔍 Testing configuration loading...")
        
        # Test core personality
        if self.stitcher.core_personality:
            self.log_test("Core personality loaded", True, f"Name: {self.stitcher.core_personality.get('name', 'Unknown')}")
        else:
            self.log_test("Core personality loaded", False, "Failed to load core personality")
        
        # Test moods
        mood_count = len(self.stitcher.moods)
        self.log_test("Moods loaded", mood_count > 0, f"Found {mood_count} moods: {list(self.stitcher.moods.keys())}")
        
        # Test functions
        func_count = len(self.stitcher.functions)
        self.log_test("Functions loaded", func_count > 0, f"Found {func_count} functions: {list(self.stitcher.functions.keys())}")
    
    def test_basic_prompt_assembly(self):
        """Test 2: Test basic prompt assembly without mood/function"""
        print("\n🧩 Testing basic prompt assembly...")
        
        message = self.test_messages["casual"]
        
        try:
            system_prompt, user_message = asyncio.run(
                self.stitcher.build_prompt(message)
            )
            
            # Check that system prompt contains core personality
            has_core = "Tova" in system_prompt and "cat-eared" in system_prompt
            self.log_test("Basic system prompt", has_core, f"Length: {len(system_prompt)} chars")
            
            # Check that user message is preserved
            has_user_message = message in user_message
            self.log_test("User message preservation", has_user_message, f"User message: {user_message[:50]}...")
            
        except Exception as e:
            self.log_test("Basic prompt assembly", False, str(e))
    
    def test_mood_combinations(self):
        """Test 3: Test all mood combinations"""
        print("\n😊 Testing mood combinations...")
        
        message = self.test_messages["casual"]
        
        for mood_name in self.stitcher.moods.keys():
            try:
                system_prompt, user_message = asyncio.run(
                    self.stitcher.build_prompt(message, mood=mood_name)
                )
                
                # Check that mood is included
                mood_config = self.stitcher.moods[mood_name]
                mood_prompt = mood_config.get("prompt_addition", "")
                
                if mood_prompt:
                    has_mood = any(keyword in system_prompt for keyword in mood_prompt.split()[:5])
                    self.log_test(f"Mood: {mood_name}", has_mood, f"Length: {len(system_prompt)} chars")
                else:
                    self.log_test(f"Mood: {mood_name}", False, "No prompt_addition found")
                    
            except Exception as e:
                self.log_test(f"Mood: {mood_name}", False, str(e))
    
    def test_function_combinations(self):
        """Test 4: Test all function combinations"""
        print("\n⚙️ Testing function combinations...")
        
        message = self.test_messages["casual"]
        
        for func_name in self.stitcher.functions.keys():
            try:
                system_prompt, user_message = asyncio.run(
                    self.stitcher.build_prompt(message, function=func_name)
                )
                
                # Check that function is included
                func_config = self.stitcher.functions[func_name]
                func_prompt = func_config.get("prompt_addition", "")
                
                if func_prompt:
                    has_function = any(keyword in system_prompt for keyword in func_prompt.split()[:5])
                    self.log_test(f"Function: {func_name}", has_function, f"Length: {len(system_prompt)} chars")
                else:
                    self.log_test(f"Function: {func_name}", False, "No prompt_addition found")
                    
            except Exception as e:
                self.log_test(f"Function: {func_name}", False, str(e))
    
    def test_mood_function_combinations(self):
        """Test 5: Test all mood + function combinations"""
        print("\n🎭 Testing mood + function combinations...")
        
        message = self.test_messages["complex"]
        
        for mood_name in self.stitcher.moods.keys():
            for func_name in self.stitcher.functions.keys():
                try:
                    system_prompt, user_message = asyncio.run(
                        self.stitcher.build_prompt(message, mood=mood_name, function=func_name)
                    )
                    
                    # Check that both mood and function are included
                    mood_config = self.stitcher.moods[mood_name]
                    func_config = self.stitcher.functions[func_name]
                    
                    mood_prompt = mood_config.get("prompt_addition", "")
                    func_prompt = func_config.get("prompt_addition", "")
                    
                    has_mood = mood_prompt and any(keyword in system_prompt for keyword in mood_prompt.split()[:3])
                    has_function = func_prompt and any(keyword in system_prompt for keyword in func_prompt.split()[:3])
                    
                    test_name = f"Mood+Function: {mood_name}+{func_name}"
                    success = has_mood and has_function
                    details = f"Length: {len(system_prompt)} chars"
                    
                    self.log_test(test_name, success, details)
                    
                except Exception as e:
                    self.log_test(f"Mood+Function: {mood_name}+{func_name}", False, str(e))
    
    def test_context_integration(self):
        """Test 6: Test context integration"""
        print("\n📋 Testing context integration...")
        
        message = self.test_messages["calendar"]
        context = {
            "current_time": "14:30",
            "user_location": "San Francisco",
            "recent_conversation": "Discussed project deadline",
            "calendar_events": "Meeting at 3pm, dinner at 7pm"
        }
        
        try:
            system_prompt, user_message = asyncio.run(
                self.stitcher.build_prompt(message, context=context)
            )
            
            # Check that context is included in user message
            has_context = "Relevant Context:" in user_message
            has_context_items = all(key in user_message for key in ["current_time", "user_location"])
            
            self.log_test("Context integration", has_context and has_context_items, 
                         f"Context items: {len(context)}")
            
        except Exception as e:
            self.log_test("Context integration", False, str(e))
    
    def test_full_combinations(self):
        """Test 7: Test full combinations with mood + function + context"""
        print("\n🎪 Testing full combinations...")
        
        message = self.test_messages["complex"]
        context = {
            "current_time": "09:00",
            "user_mood": "focused",
            "work_context": "Deadline approaching"
        }
        
        # Test a few key combinations
        test_combinations = [
            ("focused", "personal_assistant"),
            ("excited", "restaurant_assistant"),
            ("sleepy", None),
            (None, "personal_assistant")
        ]
        
        for mood, function in test_combinations:
            try:
                system_prompt, user_message = asyncio.run(
                    self.stitcher.build_prompt(message, mood=mood, function=function, context=context)
                )
                
                # Basic validation
                has_core = "Tova" in system_prompt
                has_context = "Relevant Context:" in user_message
                has_user_message = message in user_message
                
                success = has_core and has_context and has_user_message
                
                combo_name = f"Full: {mood or 'none'}+{function or 'none'}+context"
                self.log_test(combo_name, success, f"Length: {len(system_prompt)} chars")
                
            except Exception as e:
                combo_name = f"Full: {mood or 'none'}+{function or 'none'}+context"
                self.log_test(combo_name, False, str(e))
    
    def test_prompt_quality(self):
        """Test 8: Test prompt quality and coherence"""
        print("\n✨ Testing prompt quality...")
        
        message = "Tell me about yourself"
        
        try:
            system_prompt, user_message = asyncio.run(
                self.stitcher.build_prompt(message, mood="focused", function="personal_assistant")
            )
            
            # Check for key personality elements
            has_personality = all(keyword in system_prompt.lower() for keyword in 
                                ["tova", "cat-eared", "fierce", "loyal"])
            
            # Check for mood elements
            has_mood = "focused" in system_prompt.lower() or "work mode" in system_prompt.lower()
            
            # Check for function elements
            has_function = "personal assistant" in system_prompt.lower() or "calendar" in system_prompt.lower()
            
            # Check for coherence (no obvious conflicts)
            has_conflicts = ("sleepy" in system_prompt.lower() and "focused" in system_prompt.lower())
            
            success = has_personality and has_mood and has_function and not has_conflicts
            
            self.log_test("Prompt quality", success, 
                         f"Personality: {has_personality}, Mood: {has_mood}, Function: {has_function}")
            
        except Exception as e:
            self.log_test("Prompt quality", False, str(e))
    
    def test_legacy_compatibility(self):
        """Test 9: Test legacy build_prompt_legacy method"""
        print("\n🔄 Testing legacy compatibility...")
        
        message = self.test_messages["casual"]
        
        try:
            legacy_prompt = asyncio.run(
                self.stitcher.build_prompt_legacy(message, mood="excited", function="restaurant_assistant")
            )
            
            # Check that legacy method returns a single string
            is_string = isinstance(legacy_prompt, str)
            has_user_prefix = "User:" in legacy_prompt
            has_tova_suffix = "Tova:" in legacy_prompt
            
            success = is_string and has_user_prefix and has_tova_suffix
            
            self.log_test("Legacy compatibility", success, f"Length: {len(legacy_prompt)} chars")
            
        except Exception as e:
            self.log_test("Legacy compatibility", False, str(e))
    
    def show_sample_prompts(self):
        """Show sample prompts for manual inspection"""
        print("\n📝 Sample prompts for inspection:")
        print("=" * 60)
        
        message = "I need help with my schedule and I'm feeling focused"
        context = {"current_time": "10:00", "work_mode": "active"}
        
        # Sample 1: Basic
        system_prompt, user_message = asyncio.run(
            self.stitcher.build_prompt(message)
        )
        print("\n1. BASIC PROMPT:")
        print(f"System: {system_prompt[:200]}...")
        print(f"User: {user_message}")
        
        # Sample 2: With mood
        system_prompt, user_message = asyncio.run(
            self.stitcher.build_prompt(message, mood="focused")
        )
        print("\n2. WITH MOOD (focused):")
        print(f"System: {system_prompt[:200]}...")
        print(f"User: {user_message}")
        
        # Sample 3: With function
        system_prompt, user_message = asyncio.run(
            self.stitcher.build_prompt(message, function="personal_assistant")
        )
        print("\n3. WITH FUNCTION (personal_assistant):")
        print(f"System: {system_prompt[:200]}...")
        print(f"User: {user_message}")
        
        # Sample 4: Full combination
        system_prompt, user_message = asyncio.run(
            self.stitcher.build_prompt(message, mood="focused", function="personal_assistant", context=context)
        )
        print("\n4. FULL COMBINATION:")
        print(f"System: {system_prompt[:200]}...")
        print(f"User: {user_message}")
    
    def run_all_tests(self):
        """Run all prompt stitching tests"""
        print("🧪 TOVA Prompt Stitching Test Suite")
        print("=" * 60)
        
        self.test_config_loading()
        self.test_basic_prompt_assembly()
        self.test_mood_combinations()
        self.test_function_combinations()
        self.test_mood_function_combinations()
        self.test_context_integration()
        self.test_full_combinations()
        self.test_prompt_quality()
        self.test_legacy_compatibility()
        
        # Show sample prompts
        self.show_sample_prompts()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        
        if passed == total:
            print("🎉 All prompt stitching tests passed!")
            return True
        else:
            print("❌ Some tests failed. Check the output above.")
            return False

async def main():
    """Main test runner"""
    tester = PromptStitchingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Prompt stitching system is working correctly!")
        print("All combinations of core personality, moods, and functions are properly assembled.")
    else:
        print("\n⚠️  Please fix the failing tests before proceeding.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main()) 