#!/usr/bin/env python3
"""
Test Linear Integration
"""

import os
from linear_integration import LinearIntegration

def test_linear_connection():
    """Test connection to Linear API"""
    print("🧪 Testing Linear Integration...")
    
    # Check if API key is configured
    api_key = os.getenv('LINEAR_API_KEY')
    if not api_key or api_key == 'your_linear_api_key_here':
        print("❌ Linear API key not configured")
        print("📝 Please:")
        print("   1. Get your API key from https://linear.app/settings/api")
        print("   2. Copy linear_config.env to .env")
        print("   3. Fill in your LINEAR_API_KEY")
        return False
    
    try:
        linear = LinearIntegration()
        
        # Test getting issues
        print("📋 Fetching issues...")
        issues = linear.get_issues(limit=5)
        
        if issues:
            print(f"✅ Found {len(issues)} issues:")
            for issue in issues:
                print(f"   - {issue['identifier']}: {issue['title']}")
                print(f"     State: {issue['state']['name']}")
                print(f"     URL: {issue['url']}")
        else:
            print("ℹ️  No issues found (this might be normal for a new project)")
        
        print("🎉 Linear integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Linear integration: {e}")
        return False

if __name__ == "__main__":
    test_linear_connection()
