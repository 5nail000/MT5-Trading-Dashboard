# Linear Setup Guide

## 🚀 Quick Start

### 1. Get Linear API Key

1. Go to [Linear API Settings](https://linear.app/settings/api)
2. Click "Create API Key"
3. Give it a name (e.g., "MT5 Dashboard Integration")
4. Copy the generated API key

### 2. Configure Environment

1. Copy the configuration file:
   ```bash
   cp linear_config.env .env
   ```

2. Edit `.env` and add your API key:
   ```bash
   LINEAR_API_KEY=lin_api_your_actual_api_key_here
   ```

### 3. Test Integration

Run the test script:
```bash
python test_linear.py
```

### 4. Sync with Linear

Sync your commits with Linear:
```bash
python linear_sync.py
```

## 📋 Available Commands

### Create New Issue
```python
from linear_integration import LinearIntegration

linear = LinearIntegration()
result = linear.create_issue(
    title="New Feature: Add dark mode",
    description="Add dark mode support to the dashboard",
    priority=2
)
```

### Update Issue Status
```python
# Update issue MT5-3 to "In Progress"
linear.update_issue_status("MT5-3", "in_progress")

# Mark as completed
linear.update_issue_status("MT5-3", "completed")
```

### List All Issues
```python
issues = linear.get_issues()
for issue in issues:
    print(f"{issue['identifier']}: {issue['title']}")
```

## 🔗 Linear Project Links

- **Project**: https://linear.app/mt5-trading-dashboard
- **Issue MT5-3**: https://linear.app/mt5-trading-dashboard/issue/MT5-3/connect-your-tools-3
- **API Settings**: https://linear.app/settings/api

## 🛠️ Troubleshooting

### Common Issues

1. **"API key not configured"**
   - Make sure you copied `linear_config.env` to `.env`
   - Verify your API key is correct

2. **"Authentication failed"**
   - Check if your API key is valid
   - Ensure you have access to the Linear team

3. **"Team not found"**
   - Verify the team ID in your configuration
   - Make sure you're a member of the Linear team

### Getting Help

- Check Linear documentation: https://linear.app/docs
- Review API reference: https://linear.app/docs/api
- Contact Linear support if needed
