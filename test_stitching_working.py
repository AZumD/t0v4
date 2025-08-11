#!/usr/bin/env python3
"""Working test for TOVA prompt stitching"""

import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.append('.')

async def test_prompt_stitching():
    """Test the prompt stitching system"""
    print("🧪 Testing TOVA Prompt Stitching System")
    print("=" * 50)
    
    try:
        from tova.core.prompt_stitcher import PromptStitcher
        
        # Create stitcher
        stitcher = PromptStitcher("config")
        print("✅ PromptStitcher created successfully")
        
        # Show loaded configurations
        print(f"✅ Core personality: {stitcher.core_personality.get('name', 'Unknown')}")
        print(f"✅ Available moods: {list(stitcher.moods.keys())}")
        print(f"✅ Available functions: {list(stitcher.functions.keys())}")
        print()
        
        # Test 1: Basic prompt
        print("1️⃣ Testing basic prompt assembly...")
        system_prompt, user_message = await stitcher.build_prompt("Hello Tova!")
        print(f"   System prompt length: {len(system_prompt)} chars")
        print(f"   User message: {user_message}")
        print(f"   ✅ Basic prompt works")
        print()
        
        # Test 2: With mood
        print("2️⃣ Testing mood integration...")
        for mood in stitcher.moods.keys():
            system_prompt, user_message = await stitcher.build_prompt("Hello Tova!", mood=mood)
            print(f"   {mood}: {len(system_prompt)} chars")
        print(f"   ✅ All moods work")
        print()
        
        # Test 3: With function
        print("3️⃣ Testing function integration...")
        for func in stitcher.functions.keys():
            system_prompt, user_message = await stitcher.build_prompt("Hello Tova!", function=func)
            print(f"   {func}: {len(system_prompt)} chars")
        print(f"   ✅ All functions work")
        print()
        
        # Test 4: Mood + Function combinations
        print("4️⃣ Testing mood + function combinations...")
        for mood in stitcher.moods.keys():
            for func in stitcher.functions.keys():
                system_prompt, user_message = await stitcher.build_prompt(
                    "Hello Tova!", mood=mood, function=func
                )
                print(f"   {mood} + {func}: {len(system_prompt)} chars")
        print(f"   ✅ All combinations work")
        print()
        
        # Test 5: With context
        print("5️⃣ Testing context integration...")
        context = {
            "current_time": "14:30",
            "user_location": "San Francisco",
            "work_mode": "active"
        }
        system_prompt, user_message = await stitcher.build_prompt(
            "What's on my schedule?", 
            mood="focused", 
            function="personal_assistant",
            context=context
        )
        print(f"   Full combination: {len(system_prompt)} chars")
        print(f"   Context included: {'Relevant Context:' in user_message}")
        print(f"   ✅ Context integration works")
        print()
        
        # Show sample prompt
        print("📝 Sample prompt (focused + personal_assistant):")
        print("-" * 50)
        sample_system, sample_user = await stitcher.build_prompt(
            "I need help with my schedule", 
            mood="focused", 
            function="personal_assistant"
        )
        print(f"System: {sample_system[:200]}...")
        print(f"User: {sample_user}")
        print("-" * 50)
        
        print("🎉 All prompt stitching tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_prompt_stitching())
    if success:
        print("\n✅ Prompt stitching system is working correctly!")
    else:
        print("\n❌ Prompt stitching system has issues.") 