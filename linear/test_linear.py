#!/usr/bin/env python3
"""
Test Linear Integration
"""

import os
import requests
from dotenv import load_dotenv
from linear_integration import LinearIntegration

# Load environment variables from .env file
load_dotenv()

def test_linear_connection():
    """Test connection to Linear API"""
    print("🧪 Testing Linear Integration...")
    
    # Check if API key is configured
    api_key = os.getenv('LINEAR_API_KEY')
    team_id = os.getenv('LINEAR_TEAM_ID')
    
    print(f"🔑 API Key: {api_key[:20]}..." if api_key else "❌ No API Key")
    print(f"👥 Team ID: {team_id}")
    
    if not api_key or api_key == 'your_linear_api_key_here':
        print("❌ Linear API key not configured")
        print("📝 Please:")
        print("   1. Get your API key from https://linear.app/settings/api")
        print("   2. Copy linear_config.env to .env")
        print("   3. Fill in your LINEAR_API_KEY")
        return False
    
    try:
        linear = LinearIntegration()
        
        # Test getting teams first
        print("👥 Fetching teams...")
        teams_query = """
        query Teams {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """
        
        response = requests.post(
            linear.base_url,
            headers=linear.headers,
            json={"query": teams_query}
        )
        
        if response.status_code == 200:
            teams_data = response.json()
            teams = teams_data.get('data', {}).get('teams', {}).get('nodes', [])
            print(f"✅ Found {len(teams)} teams:")
            for team in teams:
                print(f"   - {team['key']}: {team['name']} (ID: {team['id']})")
        else:
            print(f"❌ Error fetching teams: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Test getting issues
        print("📋 Fetching issues...")
        issues = linear.get_issues(limit=10)
        
        if issues:
            print(f"✅ Found {len(issues)} issues:")
            for issue in issues:
                print(f"   - {issue['identifier']}: {issue['title']}")
                print(f"     State: {issue['state']['name']}")
                print(f"     URL: {issue['url']}")
        else:
            print("ℹ️  No issues found")
            print("🔍 This might be because:")
            print("   1. Team ID is incorrect")
            print("   2. No issues exist in this team")
            print("   3. API permissions issue")
        
        print("🎉 Linear integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Linear integration: {e}")
        return False

if __name__ == "__main__":
    test_linear_connection()
