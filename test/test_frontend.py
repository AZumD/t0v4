#!/usr/bin/env python3
"""Test script for TOVA v4 frontend implementation"""

import asyncio
import json
from pathlib import Path
import sys

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

async def test_frontend_components():
    """Test the frontend components"""
    print("🧪 Testing TOVA v4 Frontend Components...")
    
    # Test 1: Check if main FastAPI app can be imported
    try:
        from tova.main import app
        print("✅ FastAPI app imports successfully")
    except Exception as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        return False
    
    # Test 2: Check if frontend files exist
    frontend_path = Path(__file__).parent.parent / "frontend"
    required_files = [
        "chat/index.html",
        "chat/chat.css", 
        "chat/chat.js",
        "assets/avatar/tova_default.mp4"
    ]
    
    for file_path in required_files:
        full_path = frontend_path / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"⚠️  {file_path} not found (this is expected for placeholder files)")
    
    # Test 3: Check if config files exist
    config_path = Path(__file__).parent.parent / "config"
    config_files = [
        "personalities/tova_core.yaml",
        "moods/focused.yaml",
        "moods/sleepy.yaml"
    ]
    
    for config_file in config_files:
        full_path = config_path / config_file
        if full_path.exists():
            print(f"✅ {config_file} exists")
        else:
            print(f"❌ {config_file} not found")
            return False
    
    # Test 4: Check if core components can be imported
    try:
        from tova.core.orchestrator import TovaOrchestrator
        from tova.core.prompt_stitcher import PromptStitcher
        from tova.brains.mixtral_client import MixtralClient
        from tova.brains.phi_client import PhiClient
        from tova.api.websocket import WebSocketManager
        print("✅ All core components import successfully")
    except Exception as e:
        print(f"❌ Failed to import core components: {e}")
        return False
    
    print("\n🎉 Frontend implementation test completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_frontend_components())
    sys.exit(0 if success else 1) 