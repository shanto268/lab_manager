# LFL Lab Manager

This project serves as a lab manager for the [Levenson-Falk Lab](https://dornsife.usc.edu/lfl/) at USC. Presently, it automates reminders for maintenance, snacks, and manages lab meeting schedules through emails, Slack and Google Calendar.

## Project Structure

- `.github/`: Contains GitHub workflows for automation.
- `calendar_manager.py`: Manages Google Calendar integration.
- `config_loader.py`: Loads configuration from JSON files.
- `email_notifier.py`: Handles email notifications.
- `main.py`: The main script for managing notifications.
- `slack_notifier.py`: Manages Slack notifications.
- `duty_tracker.json`: Tracks the rotation of lab duties.

## Setup and Operation

1. **Local Setup**:
   - Install dependencies from `requirements.txt`.
   - Set up environment variables for Gmail, Slack, and Google Calendar credentials.
   - Use `client_secret.json` and `token.pickle` for Google Calendar API.

2. **PythonAnywhere Setup**:
   - Upload the script files to PythonAnywhere.
   - Set up a scheduled task to run `main.py` daily at 7 AM.
   - Ensure `client_secret.json` and `token.pickle` are safely uploaded and handled.

3. **Handling Authentication**:
   - The script checks the validity of `token.pickle`.
   - If re-authentication is required, it sends an email notification.
   - Manually update `token.pickle` on PythonAnywhere after re-authenticating locally.

**Note**: For security, never store sensitive information like lab members' details and service keys in the repository.

## GitHub Actions

The project *can* be configured to use the GitHub Action defined in `.github/workflows/main.yml` to automate reminders.

## Security

Sensitive information is handled securely, and environment variables are used to store credentials.

---

**Remember to keep the `token.pickle` and `client_secret.json` files secure and handle them carefully during deployment and updates.**
