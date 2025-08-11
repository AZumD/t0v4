#!/usr/bin/env python3
"""Simple test for TOVA prompt stitching"""

import sys
import os
from pathlib import Path
import asyncio

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

try:
    from tova.core.prompt_stitcher import PromptStitcher
    print("✅ PromptStitcher imported successfully")
    
    # Test basic functionality
    stitcher = PromptStitcher("config")
    print("✅ PromptStitcher instance created successfully")
    
    # Test configuration loading
    print(f"✅ Core personality: {stitcher.core_personality.get('name', 'Unknown')}")
    print(f"✅ Moods loaded: {list(stitcher.moods.keys())}")
    print(f"✅ Functions loaded: {list(stitcher.functions.keys())}")
    
    # Test basic prompt assembly
    async def test_basic():
        system_prompt, user_message = await stitcher.build_prompt("Hello Tova!")
        print(f"✅ Basic prompt assembled: {len(system_prompt)} chars")
        print(f"✅ User message: {user_message}")
        return True
    
    # Test with mood
    async def test_mood():
        system_prompt, user_message = await stitcher.build_prompt("Hello Tova!", mood="focused")
        print(f"✅ Mood prompt assembled: {len(system_prompt)} chars")
        return True
    
    # Test with function
    async def test_function():
        system_prompt, user_message = await stitcher.build_prompt("Hello Tova!", function="personal_assistant")
        print(f"✅ Function prompt assembled: {len(system_prompt)} chars")
        return True
    
    # Test full combination
    async def test_full():
        system_prompt, user_message = await stitcher.build_prompt(
            "Hello Tova!", 
            mood="focused", 
            function="personal_assistant",
            context={"time": "10:00", "mode": "work"}
        )
        print(f"✅ Full prompt assembled: {len(system_prompt)} chars")
        return True
    
    # Run tests
    async def run_tests():
        await test_basic()
        await test_mood()
        await test_function()
        await test_full()
        print("✅ All prompt stitching tests passed!")
    
    asyncio.run(run_tests())
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 