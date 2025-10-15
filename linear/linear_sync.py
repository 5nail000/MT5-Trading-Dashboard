#!/usr/bin/env python3
"""
Linear-GitHub Integration Script
Automatically sync Linear issues with GitHub commits
"""

import os
import subprocess
import json
from datetime import datetime
from linear_integration import LinearIntegration

class LinearGitHubSync:
    """Sync Linear issues with GitHub commits"""
    
    def __init__(self):
        self.linear = LinearIntegration()
    
    def get_last_commit_message(self) -> str:
        """Get the last commit message"""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
    
    def get_last_commit_hash(self) -> str:
        """Get the last commit hash"""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%H"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""
    
    def create_issue_from_commit(self, commit_message: str, commit_hash: str) -> Dict:
        """Create Linear issue from commit message"""
        # Extract issue type and description from commit message
        if ":" in commit_message:
            title_part, description_part = commit_message.split(":", 1)
            title = f"Commit: {title_part.strip()}"
            description = f"**Commit Hash:** {commit_hash}\n\n**Description:** {description_part.strip()}"
        else:
            title = f"Commit: {commit_message}"
            description = f"**Commit Hash:** {commit_hash}\n\n**Description:** {commit_message}"
        
        return self.linear.create_issue(title, description)
    
    def update_issue_status(self, issue_identifier: str, status: str) -> Dict:
        """Update issue status"""
        # Map status names to Linear state names
        status_mapping = {
            "completed": "Done",
            "fixed": "Done", 
            "resolved": "Done",
            "in_progress": "In Progress",
            "started": "In Progress"
        }
        
        linear_status = status_mapping.get(status.lower(), status)
        
        # Get issue by identifier
        issue = self.linear.get_issue_by_identifier(issue_identifier)
        if issue:
            return self.linear.update_issue(issue['id'], state={'name': linear_status})
        
        return {"error": "Issue not found"}
    
    def sync_with_linear(self):
        """Main sync function"""
        print("🔄 Syncing with Linear...")
        
        # Get recent commits
        commit_message = self.get_last_commit_message()
        commit_hash = self.get_last_commit_hash()
        
        if commit_message:
            print(f"📝 Last commit: {commit_message}")
            
            # Check if commit message contains issue reference
            if any(keyword in commit_message.lower() for keyword in ['fix', 'resolve', 'complete', 'close']):
                print("✅ Commit appears to resolve an issue")
                # You can add logic here to automatically close related issues
            else:
                print("📋 Creating new issue from commit")
                result = self.create_issue_from_commit(commit_message, commit_hash)
                if result.get('data', {}).get('issueCreate', {}).get('success'):
                    issue = result['data']['issueCreate']['issue']
                    print(f"✅ Created issue: {issue['identifier']} - {issue['title']}")
                    print(f"🔗 URL: {issue['url']}")
                else:
                    print("❌ Failed to create issue")
        
        print("🎉 Sync completed!")

def main():
    """Main function"""
    sync = LinearGitHubSync()
    sync.sync_with_linear()

if __name__ == "__main__":
    main()
