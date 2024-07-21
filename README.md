# LFL Lab Manager

This project serves as a lab manager for the [Levenson-Falk Lab](https://dornsife.usc.edu/lfl/) at USC. It automates reminders for maintenance, snacks, and manages lab meeting schedules through emails, Slack, and Google Calendar.

# Table of Contents

- [LFL Lab Manager](#lfl-lab-manager)
  - [Project Structure](#project-structure)
  - [Setup and Operation](#setup-and-operation)
    - [Local Setup](#local-setup)
    - [GitHub Actions Setup](#github-actions-setup)
    - [PythonAnywhere Setup](#pythonanywhere-setup)
    - [Handling Authentication](#handling-authentication)
    - [Mac Setup for Scheduled Execution](#mac-setup-for-scheduled-execution)
- [mm_calendar.py Overview](#mm_calendarpy-overview)
  - [Features](#features)
  - [Usage](#usage)
  - [Setup](#setup)
- [Security](#security)

## Project Structure

- `.github/`: Contains GitHub workflows for automation.
- `calendar_manager.py`: Manages Google Calendar integration.
- `config_loader.py`: Loads configuration from JSON files.
- `email_notifier.py`: Handles email notifications.
- `main.py`: The main script for managing notifications.
- `slack_notifier.py`: Manages Slack notifications.
- `duty_tracker.json`: Tracks the rotation of lab duties.
- `trigger.sh`: Script for running `main.py` in a scheduled manner.
- `check_and_trigger.sh`: Checks for missed executions and triggers `main.py` if needed.
- `markers/`: Directory where the marker file emissions are stored.
-

## Setup and Operation

### Local Setup

1. **Install Dependencies:**
   Install the necessary dependencies from `requirements.txt`.

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables:**
   Set up environment variables for Gmail, Slack, and Google Calendar credentials.

   ```bash
   export GMAIL_USER=<email>
   export GMAIL_PASSWORD=<password>
   export SLACK_TOKEN=<token>
   ```

3. **Generate and Encrypt Sensitive Files:**
   Move or generate the `client_secret.json`, `token.pickle`, `service_key.json`, and `lab_members.json` files locally. Encrypt these files using the following commands:

   ```bash
   openssl aes-256-cbc -salt -a -e -in client_secret.json -out client_secret.json.enc -pass pass:$SECRET_KEY -pbkdf2
   openssl aes-256-cbc -salt -a -e -in token.pickle -out token.pickle.enc -pass pass:$SECRET_KEY -pbkdf2
   openssl aes-256-cbc -salt -a -e -in service_key.json -out service_key.json.enc -pass pass:$SECRET_KEY -pbkdf2
   openssl aes-256-cbc -salt -a -e -in lab_members.json -out lab_members.json.enc -pass pass:$SECRET_KEY -pbkdf2
   ```

4. **Commit Encrypted Files to Repository:**
   Commit and push the encrypted files (`*.enc`) to your repository.

### GitHub Actions Setup

1. **Create GitHub Secrets:**
   Go to your GitHub repository settings, navigate to `Secrets and variables` -> `Actions`, and add the following secrets:

   - `SECRET_KEY`: Your encryption password.
   - `GMAIL_USER`: Your Gmail username.
   - `GMAIL_PASSWORD`: Your Gmail password.
   - `SLACK_TOKEN`: Your Slack token.
   - `GH_BOT`: Your GitHub PAT with at least `repo` scopes enabled.

2. **Create GitHub Actions Workflow:**
   Create a workflow file in `.github/workflows/main.yml`. Check the [GitHub Actions workflow](.github/workflows/main.yml) in this repository for reference.

   The idea is to decrypt the sensitive files, set up the environment variables, and run the script using the decrypted files.

### PythonAnywhere Setup

1. **Upload Script Files:**
   Upload the script files and encrypted JSON files (`*.enc`) to PythonAnywhere.

2. **Set Up Scheduled Task:**
   Set up a scheduled task to run `main.py` daily at 7 AM using cron.

   ```bash
   0 7 * * * /home/<username>/lfl-lab-manager/venv/bin/python /home/<username>/lfl-lab-manager/main.py
   ```

3. **Upload and Decrypt Sensitive Files:**
   Ensure `client_secret.json` and `token.pickle` are safely uploaded and handled. You may need to decrypt these files on PythonAnywhere before running your script.

### Handling Authentication

- The script checks the validity of `token.pickle`.
- If re-authentication is required, it sends an email notification.
- Manually update `token.pickle` on PythonAnywhere after re-authenticating locally.

---

This updated blurb provides comprehensive instructions for setting up and running your workflow both locally and in the cloud using GitHub Actions and PythonAnywhere.

### Mac Setup for Scheduled Execution

For Mac users, a method is provided to ensure `trigger.sh` runs even if the Mac is asleep at the scheduled time:

1. **Marker System**: The `trigger.sh` script creates a daily marker file upon successful execution, indicating the script has run for that day.

2. **Missed Execution Check**: `check_and_trigger.sh` checks for the presence of this marker file. If it's missing (indicating a missed execution), it runs `trigger.sh`.

3. **`launchd` Daemon**: A `launchd` service is set up to run `check_and_trigger.sh` every time the Mac wakes up, ensuring missed executions are caught.

   - Create `com.user.checkandtrigger.plist` in `~/Library/LaunchAgents/` with the following content:
     ```xml
     <?xml version="1.0" encoding="UTF-8"?>
     <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
     <plist version="1.0">
     <dict>
         <key>Label</key>
         <string>com.user.checkandtrigger</string>
         <key>ProgramArguments</key>
         <array>
             <string>/path/to/check_and_trigger.sh</string>
         </array>
         <key>WatchPaths</key>
         <array>
             <string>/var/log/powermanagement</string>
         </array>
         <key>RunAtLoad</key>
         <true/>
     </dict>
     </plist>
     ```
   - Load the `launchd` job:
     ```bash
     launchctl load ~/Library/LaunchAgents/com.user.checkandtrigger.plist
     ```

**Note**: For security, never store sensitive information like lab members' details and service keys in the repository.

---

## mm_calendar.py Overview

The `mm_calendar.py` script automates the creation of calendar events based on a list of presentations from the APS March Meeting.

### Features

- Extracts presentation details from provided APS URLs.
- Automatically creates Google Calendar events with extracted details.
- Authenticates with Google Calendar API to manage calendar events.

### Usage

1. Ensure Google Calendar API credentials are set up and `credentials.json` is available.
2. Populate `url_list` in `mm_calendar.py` with APS meeting URLs to schedule.
3. Run `mm_calendar.py` to authenticate and create events in the specified Google Calendar.

### Setup

Follow the local setup instructions for environment variables and authentication as described in the [Setup and Operation](#setup-and-operation) section. Ensure `MM_calendar_ID` and `MM_TIMEZONE` are correctly set in your environment or `.env` file to match your Google Calendar settings.

**Important**: Keep `token.pickle` and `credentials.json` secure and update them as needed to maintain access to the Google Calendar API.

For detailed steps on handling authentication and deploying the script, refer to the [Handling Authentication](#handling-authentication) section.

---

## Security

Sensitive information is handled securely, and environment variables are used to store credentials.

**Remember to keep the `token.pickle` and `client_secret.json` files secure and handle them carefully during deployment and updates.**
