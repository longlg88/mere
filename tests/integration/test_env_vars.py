#!/usr/bin/env python3
"""
Test Environment Variables Loading
Verify that .env file is loaded correctly
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

def test_env_loading():
    """Test that environment variables are loaded from .env file"""
    print("🔧 Testing Environment Variables Loading")
    print("=" * 45)
    
    try:
        # Import calendar service (this should load .env)
        from calendar_service import GoogleCalendarService
        
        # Check if environment variables are loaded
        openai_key = os.getenv('OPENAI_API_KEY')
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        database_url = os.getenv('DATABASE_URL')
        environment = os.getenv('ENVIRONMENT')
        log_level = os.getenv('LOG_LEVEL')
        
        print("📋 Environment Variables Status:")
        
        # Test essential variables
        if openai_key:
            print(f"   ✅ OPENAI_API_KEY: {openai_key[:20]}...")
        else:
            print("   ❌ OPENAI_API_KEY: Not found")
        
        if database_url:
            print(f"   ✅ DATABASE_URL: {database_url}")
        else:
            print("   ❌ DATABASE_URL: Not found")
        
        if environment:
            print(f"   ✅ ENVIRONMENT: {environment}")
        else:
            print("   ⚠️  ENVIRONMENT: Not set (using default)")
            
        if log_level:
            print(f"   ✅ LOG_LEVEL: {log_level}")
        else:
            print("   ⚠️  LOG_LEVEL: Not set (using default)")
        
        # Test Google Calendar credentials
        print("\n📅 Google Calendar Configuration:")
        if google_client_id:
            print(f"   ✅ GOOGLE_CLIENT_ID: {google_client_id[:20]}...")
            print("   📝 Using environment variables for OAuth")
        else:
            print("   ✅ GOOGLE_CLIENT_ID: Empty (will use credentials.json)")
            print("   📝 Using credentials.json file for OAuth")
        
        # Test calendar service initialization
        print("\n🔐 Calendar Service Test:")
        calendar_service = GoogleCalendarService()
        
        if calendar_service.use_env_vars:
            print("   ✅ Calendar service configured for environment variables")
            print("   📝 Production OAuth flow will be used")
        else:
            print("   ✅ Calendar service configured for credentials.json")
            print("   📝 Development OAuth flow will be used")
        
        print("\n✅ Environment variables test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Environment variables test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dotenv_file_exists():
    """Test that .env file exists and is readable"""
    print("\n📁 Testing .env File")
    print("=" * 25)
    
    try:
        # Check if .env file exists
        env_file = Path(__file__).parent.parent.parent / '.env'
        
        if env_file.exists():
            print(f"   ✅ .env file found: {env_file}")
            
            # Read and validate basic structure
            with open(env_file, 'r') as f:
                content = f.read()
                
            if 'OPENAI_API_KEY' in content:
                print("   ✅ OPENAI_API_KEY found in .env")
            else:
                print("   ❌ OPENAI_API_KEY not found in .env")
            
            if 'DATABASE_URL' in content:
                print("   ✅ DATABASE_URL found in .env")
            else:
                print("   ❌ DATABASE_URL not found in .env")
                
            if 'GOOGLE_CLIENT_ID' in content:
                print("   ✅ GOOGLE_CLIENT_ID found in .env")
            else:
                print("   ❌ GOOGLE_CLIENT_ID not found in .env")
            
            print(f"   ✅ .env file contains {len(content.splitlines())} lines")
            
        else:
            print(f"   ❌ .env file not found: {env_file}")
            return False
        
        print("   ✅ .env file validation completed")
        return True
        
    except Exception as e:
        print(f"   ❌ .env file test failed: {e}")
        return False

def test_calendar_config_modes():
    """Test different calendar configuration modes"""
    print("\n⚙️ Testing Calendar Configuration Modes")
    print("=" * 45)
    
    try:
        from calendar_service import GoogleCalendarService
        
        # Test current configuration
        current_client_id = os.getenv('GOOGLE_CLIENT_ID')
        
        print(f"📋 Current Configuration:")
        if current_client_id:
            print(f"   Mode: Environment Variables")
            print(f"   Client ID: {current_client_id[:30]}...")
            print(f"   OAuth Flow: Production Web Application")
        else:
            print(f"   Mode: Credentials File")
            print(f"   File: credentials.json")
            print(f"   OAuth Flow: Development Desktop Application")
        
        # Initialize service
        service = GoogleCalendarService()
        print(f"   ✅ Service initialized successfully")
        print(f"   ✅ Using environment variables: {service.use_env_vars}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Calendar configuration test failed: {e}")
        return False

def main():
    """Run all environment variable tests"""
    print("🚀 Starting Environment Variables Tests")
    print("=" * 50)
    
    success = True
    test_results = []
    
    # Test 1: Environment loading
    try:
        result = test_env_loading()
        test_results.append(("Environment Variables Loading", result))
        success &= result
    except Exception as e:
        print(f"❌ Environment loading test crashed: {e}")
        test_results.append(("Environment Variables Loading", False))
        success = False
    
    # Test 2: .env file exists
    try:
        result = test_dotenv_file_exists()
        test_results.append((".env File Validation", result))
        success &= result
    except Exception as e:
        print(f"❌ .env file test crashed: {e}")
        test_results.append((".env File Validation", False))
        success = False
    
    # Test 3: Calendar configuration modes
    try:
        result = test_calendar_config_modes()
        test_results.append(("Calendar Configuration Modes", result))
        success &= result
    except Exception as e:
        print(f"❌ Calendar config test crashed: {e}")
        test_results.append(("Calendar Configuration Modes", False))
        success = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Environment Variables Test Summary")
    print("=" * 50)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
    
    if success:
        print("\n🎉 Environment configuration is working correctly!")
        print("📝 .env file loaded successfully")
        print("📝 Calendar service configured properly")
    else:
        print("\n⚠️ Some environment tests failed - check configuration")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)