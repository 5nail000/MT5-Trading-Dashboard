#!/usr/bin/env python3
"""
Linear API Integration for MT5 Trading Dashboard
"""

import os
import requests
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LinearIntegration:
    """Linear API integration class"""
    
    def __init__(self, api_key: str = None, team_id: str = None):
        self.api_key = api_key or os.getenv('LINEAR_API_KEY')
        self.team_id = team_id or os.getenv('LINEAR_TEAM_ID', 'mt5-trading-dashboard')
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
    
    def create_issue(self, title: str, description: str = "", 
                    priority: int = 3, state_id: str = None) -> Dict:
        """Create a new issue in Linear"""
        query = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """
        
        variables = {
            "input": {
                "title": title,
                "description": description,
                "priority": priority,
                "teamId": self.team_id,
                "stateId": state_id
            }
        }
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": query, "variables": variables}
        )
        
        return response.json()
    
    def get_issues(self, limit: int = 50) -> List[Dict]:
        """Get list of issues"""
        query = """
        query Issues($first: Int!, $filter: IssueFilter) {
            issues(first: $first, filter: $filter) {
                nodes {
                    id
                    identifier
                    title
                    description
                    state {
                        name
                    }
                    priority
                    url
                }
            }
        }
        """
        
        variables = {
            "first": limit,
            "filter": {
                "team": {"id": {"eq": self.team_id}}
            }
        }
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": query, "variables": variables}
        )
        
        result = response.json()
        if 'data' in result and result['data']:
            return result['data'].get('issues', {}).get('nodes', [])
        return []
    
    def get_workflow_states(self) -> Dict:
        """Get available workflow states"""
        query = """
        query WorkflowStates {
            workflowStates {
                nodes {
                    id
                    name
                    type
                }
            }
        }
        """
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": query}
        )
        
        result = response.json()
        if 'data' in result and result['data']:
            return result['data'].get('workflowStates', {}).get('nodes', [])
        return []
    
    def update_issue(self, issue_id: str, **kwargs) -> Dict:
        """Update an issue"""
        # Handle state name to stateId conversion
        if 'state' in kwargs and isinstance(kwargs['state'], dict) and 'name' in kwargs['state']:
            state_name = kwargs['state']['name']
            states = self.get_workflow_states()
            
            # Find state by name
            state_id = None
            for state in states:
                if state['name'] == state_name:
                    state_id = state['id']
                    break
            
            if state_id:
                kwargs['stateId'] = state_id
                del kwargs['state']
            else:
                return {"error": f"State '{state_name}' not found"}
        
        query = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    state {
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            "id": issue_id,
            "input": kwargs
        }
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": query, "variables": variables}
        )
        
        return response.json()
    
    def get_issue_by_identifier(self, identifier: str) -> Optional[Dict]:
        """Get issue by identifier (e.g., MT5-3)"""
        query = """
        query Issue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                state {
                    name
                }
                priority
                url
            }
        }
        """
        
        variables = {"id": identifier}
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": query, "variables": variables}
        )
        
        data = response.json().get('data', {})
        return data.get('issue') if data else None

def main():
    """Main function for testing Linear integration"""
    linear = LinearIntegration()
    
    # Test getting issues
    print("Fetching issues...")
    issues = linear.get_issues()
    
    for issue in issues:
        print(f"- {issue['identifier']}: {issue['title']}")
        print(f"  State: {issue['state']['name']}")
        print(f"  URL: {issue['url']}")
        print()

if __name__ == "__main__":
    main()
