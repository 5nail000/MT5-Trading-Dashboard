# Linear Integration Configuration
# MT5 Trading Dashboard Project

## Linear Project Setup

### Project Information
- **Project Name**: MT5 Trading Dashboard
- **Project URL**: https://linear.app/mt5-trading-dashboard
- **Issue URL**: https://linear.app/mt5-trading-dashboard/issue/MT5-3/connect-your-tools-3

### Integration Steps

1. **Authentication**
   - Get API key from Linear settings
   - Configure environment variables

2. **Issue Management**
   - Create issues for new features
   - Track bug fixes
   - Monitor project progress

3. **Workflow Integration**
   - Link commits to issues
   - Automate issue updates
   - Sync with GitHub

### Environment Variables
```bash
LINEAR_API_KEY=your_api_key_here
LINEAR_TEAM_ID=mt5-trading-dashboard
```

### Commands
```bash
# Create new issue
linear issue create --title "Feature: Add new chart type" --description "Description here"

# List issues
linear issue list

# Update issue
linear issue update MT5-3 --state "In Progress"
```

### GitHub Integration
- Link Linear issues to GitHub PRs
- Automatically close issues when PRs are merged
- Sync issue status with development progress
