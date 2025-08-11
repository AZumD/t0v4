#!/usr/bin/env python3
"""Simple test for TOVA TUI"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts', 'utils'))

try:
    import tova_tui
    print("✅ TUI module imported successfully")
    
    # Test basic functionality
    tui = tova_tui.TovaTUI()
    print("✅ TUI instance created successfully")
    
    # Test service definitions
    print(f"✅ Found {len(tui.services)} services:")
    for name, service in tui.services.items():
        print(f"  - {name}: {service.display_name} (port {service.port})")
    
    # Test script existence
    for name, service in tui.services.items():
        exists = tui.check_script_exists(service.start_script)
        print(f"  - {name} script: {'✅' if exists else '❌'} {service.start_script}")
    
    print("✅ All basic tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 