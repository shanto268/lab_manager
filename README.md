# LFL Lab Manager

This project aims to serve as a lab manager for the [Levenson-Falk Lab](https://dornsife.usc.edu/lfl/) at USC.

So far, it includes features to serve as a notification system designed to automate reminders for a lab environment. It includes features for sending maintenance and snack reminders, as well as managing scheduling through Google Calendar.

## Project Structure

```
.github/
	workflows/
		main.yml
.gitignore
README.md
calendar_manager.py
config_loader.py
duty_tracker.json
email_notifier.py
main.py
slack_notifier.py
```

## Key Files

- [`main.py`](command:_github.copilot.openRelativePath?%5B%22main.py%22%5D "main.py"): The main script that orchestrates the notification system.
- [`config_loader.py`](command:_github.copilot.openRelativePath?%5B%22config_loader.py%22%5D "config_loader.py"): Module to load configuration from JSON files.
- [`email_notifier.py`](command:_github.copilot.openRelativePath?%5B%22email_notifier.py%22%5D "email_notifier.py"): Handles the email notification system.
- [`slack_notifier.py`](command:_github.copilot.openRelativePath?%5B%22slack_notifier.py%22%5D "slack_notifier.py"): Manages notifications on Slack.
- [`calendar_manager.py`](command:_github.copilot.openRelativePath?%5B%22calendar_manager.py%22%5D "calendar_manager.py"): Integrates with Google Calendar for scheduling.

## GitHub Actions

The project uses GitHub Actions for automation. The workflow configuration is in [`.github/workflows/main.yml`](command:_github.copilot.openRelativePath?%5B%22.github%2Fworkflows%2Fmain.yml%22%5D ".github/workflows/main.yml"). It includes jobs for sending maintenance and snack reminders.

## Setup

To set up the project, install the dependencies listed in `requirements.txt`. You'll also need to set up environment variables for Gmail and Slack credentials, as well as the Google Calendar service key.

Please note that this project is designed with security in mind. **Sensitive information like lab members' details and service keys should never be stored in the repository.**