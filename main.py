"""
This script is used to send reminders to lab members about their duties.
The script is run every day at 7:00 AM PST.
"""
import base64
import calendar
import json
import os
import subprocess
import sys
import traceback
from datetime import date, datetime, timedelta

import holidays

from calendar_manager import CalendarManager
from config_loader import ConfigLoader
from email_notifier import EmailNotifier
from slack_notifier import SlackNotifier

__author__ = "Sadman Ahmed Shanto"
__email__ = "shanto@usc.edu"

MEETING_SIGNATURE = "\n\nLooking Forward to it 🤩,\nLFL Bot."
SERVICE_SIGNATURE = "\n\nThank you for your service 🫡,\nLFL Bot."

def create_reminder(instruction):
    check_symbol = "-"
    # check_symbol = "-"
    return "{} {}\n".format(check_symbol, instruction)

def create_step(reminder):
    check_symbol = "☐"
    # check_symbol = "-"
    return "{} {}\n".format(check_symbol, reminder)

def get_header(name, date_maintenance):
    header = "Hi {},\n\nThis is a reminder that next week it is your turn to do the LFL Lab Maintenance. Please refer to the following checklist.\n\n".format(name)
    return header

def get_signature(bot_name="LFL Bot"):
    salute = "🫡 "
    # salute = ""
    return "\n\nThank you for your service {},\n{}".format(salute, bot_name)

def get_reminders(reminders_list):
    reminders = []
    for reminder_string in reminders_list:
        reminders.append(create_reminder(reminder_string))
    prompt = "\n\nSome safety considerations from EH&S:\n"
    reminders = "".join(reminders)
    return prompt + reminders + "\n"

def create_email_content(name, date_maintenance, instructions, reminders, bot_name="LFL Bot"):
    header = get_header(name, date_maintenance)
    steps = []
    for instruction in instructions:
        steps.append(create_step(instruction))
    body = "".join(steps)
    reminders = get_reminders(reminders)
    signature = get_signature(bot_name)
    return header + body + reminders + signature

def chosen_day(day_name):
    days = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6
    }
    return days.get(day_name, -1)  # Returns -1 if the day name is not valid

def get_decoded_service_key(base64_key):
    if base64_key:
        decoded_key = base64.b64decode(base64_key).decode('utf-8')
        return json.loads(decoded_key)
    else:
        raise ValueError("GOOGLE_CALENDAR_SERVICE_KEY is not set or is invalid")

def load_google_service_key(file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            raise ValueError(f"Failed to load Google service key: {e}")




class LabNotificationSystem:
    def __init__(self, presentation_day, presentation_time, maintenance_day, location, send_presentation_reminders):
        self.lab_members = ConfigLoader('lab_members.json').load_config()
        self.gmail_username = os.environ.get('GMAIL_USERNAME')
        self.gmail_password = os.environ.get('GMAIL_PASSWORD')
        self.slack_token = os.environ.get('SLACK_TOKEN')
        self.google_calendar_service_key = load_google_service_key('service_key.json')


        self.maintenance_day = chosen_day(maintenance_day)
        self.presentation_day = chosen_day(presentation_day)
        self.presentation_time = presentation_time
        self.location = location
        self.us_holidays = holidays.US()
        self.send_presentation_reminders = send_presentation_reminders


        self.email_notifier = EmailNotifier(self.gmail_username, self.gmail_password)
        self.calendar_manager = CalendarManager(self.email_notifier)
        self.slack_notifier = SlackNotifier(self.slack_token)

    def run(self):
        print("=====================================")
        print("Running the lab notification system...")
        print(f"Date: {date.today()} | Time: {datetime.now().strftime('%H:%M:%S')} | OS: {os.name}")
        print("=====================================")
        print("Handling Presentation reminders...")
        self.send_presentation_reminders()
        print("Handling Lab maintenance reminders...")
        self.send_lab_maintenance_reminders()
        print("Handling Lab snacks reminders...")
        self.send_lab_snacks_reminders()
        print("=====================================")
        print("\n")

    def get_next_member(self, members, current_member_id):
        current_index = members.index(next((m for m in members if m['id'] == current_member_id), None))
        next_index = (current_index + 1) % len(members)
        return members[next_index]['id']

    def update_duty_tracker(self, duty_type, next_member_id):
        with open('duty_tracker.json', 'r') as file:
            tracker = json.load(file)
        tracker[duty_type] = next_member_id
        with open('duty_tracker.json', 'w') as file:
            json.dump(tracker, file, indent=4)

    def is_there_meeting_next_week(self, today):
        # Check if next week today is a national holiday
        today = today + timedelta(days=7)
        if today in self.us_holidays:
            self.slack_notifier.send_message('#lfl-general-exclusive', f"Reminder: No lab meeting next week due to a national holiday - {self.us_holidays.get(today)}")
            return True
        # Check if today is the first presentation day of the month
        elif today.day == self.presentation_day:
            self.slack_notifier.send_message('#lfl-general-exclusive', "Reminder: Today is 'Lab Citizen Day'")
            return True
        # All else case
        else:
            return False

    def holiday_next_week(self):
        # Check if next week today is a national holiday
        next_week = datetime.today() + timedelta(days=7)
        if next_week in self.us_holidays:
            self.slack_notifier.send_message('#lfl-general-exclusive', f"Reminder: No lab meeting next week due to a national holiday - {self.us_holidays.get(next_week)}")
            return True
        else:
            return False

    def send_presentation_reminders(self):
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday() or 7))
        lab_citizen_day_td_link = os.environ.get("ONENOTE_LCD")

        # Check if today is the presentation day
        if today.weekday() == self.presentation_day:
            # Check if next Monday is the first Monday of the next month
            if (next_monday.month != today.month) and (next_monday.day <= 7):
                self.slack_notifier.send_message(
                    '#lfl-general-exclusive',
                    f"Reminder: No lab meeting next week, we will have a Lab Citizen Day on {next_monday}. Don't know what to do?\nRefer to\n{lab_citizen_day_td_link}"
                )

                pres_date = today + timedelta(days=7)

                try:
                    self.calendar_manager.create_timed_event(
                        title="Lab Citizen Day",
                        date=pres_date,
                        start_time_str=self.presentation_time,
                        attendees=self.get_all_member_emails(),
                        location=self.location,
                    )
                except Exception as e:
                    print(f"Error creating Lab Citizen Day event: {e}")
            else:
                self.send_presentation_reminder_email()
        else:
            print("No presentation reminders today")
    
    def send_presentation_reminder_email(self):
        today = datetime.today()
        tracker = self.load_duty_tracker()

        if self.holiday_next_week():
            print("No lab meeting next week due to a national holiday")
        else:
            print("tracker: ", tracker)
            current_presenter_id = tracker.get('presentation', None)
            presenters, next_presenter_id, is_group_presentation = self.get_next_presenter(current_presenter_id)

            pres_date = today + timedelta(days=7)

            # Handle group presentation for undergraduates
            if is_group_presentation:
                print("Group Presentation by undergrads")
                if self.send_presentation_reminders:
                    print("Sending presentation reminders...")
                    for presenter_info in presenters:
                        subject = "LFL Lab Meeting Presentation"
                        message = f"Hello {presenter_info['name']},\n\nYou are scheduled to present at next week's lab meeting - {pres_date}." + MEETING_SIGNATURE
                        self.email_notifier.send_email([presenter_info['email']], subject, message)

                    # Create Google Calendar event for group presentation
                    self.calendar_manager.create_timed_event(
                        title="Undergraduate Group Presentation",
                        date=pres_date,
                        start_time_str=self.presentation_time,
                        attendees=[member['email'] for member in presenters]
                    )
                else:
                    print("Presentation reminders disabled, skipping emails and calendar events")

            # Handle individual presentation
            else:
                presenter_info = presenters[0]  # Only one presenter
                print(f"Presentation by {presenter_info['name']}")
                if self.send_presentation_reminders:
                    print("Sending presentation reminders...")
                    subject = "LFL Lab Meeting Presentation"
                    message = f"Hello {presenter_info['name']},\n\nYou are scheduled to present at next week's lab meeting - {pres_date}." + MEETING_SIGNATURE
                    self.email_notifier.send_email([presenter_info['email']], subject, message)

                    # Create Google Calendar event for individual presentation
                    self.calendar_manager.create_timed_event(
                        title="Group Meeting Presentation by " + presenter_info['name'],
                        date=pres_date,
                        start_time_str=self.presentation_time,
                        attendees=[member['email'] for member in presenters],
                        location=self.location
                    )
                else:
                    print("Presentation reminders disabled, skipping emails and calendar events")

            # Update the duty tracker
            self.update_duty_tracker('presentation', next_presenter_id)

    def load_duty_tracker(self):
        with open('duty_tracker.json', 'r') as file:
            return json.load(file)

    def get_all_members(self):
        """
        Returns a list of all lab members
        """
        return list(self.lab_members.values())

    def get_all_member_emails(self):
        """
        Returns a list of all lab member emails
        """
        return [member['email'] for member in self.lab_members.values()]

    def get_next_presenter(self, current_presenter_id):
        members_list = list(self.lab_members.values())
        current_index = members_list.index(next((member for member in members_list if member['id'] == current_presenter_id), members_list[0]))

        next_index = (current_index + 1) % len(members_list)
        next_presenter = members_list[next_index]

        if next_presenter['role'] == 'Undergraduate Student':
            # Find all undergraduates
            undergrads = [member for member in members_list if member['role'] == 'Undergraduate Student']

            # Return the list of undergraduates and set the next presenter to the first non-undergraduate
            next_non_undergrad_index = (members_list.index(undergrads[-1]) + 1) % len(members_list)
            next_non_undergrad_id = members_list[next_non_undergrad_index]['id']

            return undergrads, next_non_undergrad_id, True
        else:
            # Next presenter is not an undergraduate
            return [next_presenter], next_presenter['id'], False

    def lab_maintance_email(self, recipient_name, date_maintenance):

        ln2_instruction = "Please schedule a Liquid Nitrogen Fill Up with Jivin (jseward@usc.edu) and refill our tank"

        instructions = [ln2_instruction, "Purchase any outstanding item left on the Purchasing Wish list", "After you purchase something put it on the #purchasing channel" ,"Check Lab Inventory: napkins, water filters, gloves, masks, printing supply, compressed air", "Check Chemical Inventory", "Assess Water Filter Status", "Check cooling water temperature and pressure", "Fill up traps and dewars with LN2", "General Cleanup of the Lab (call people out if needed)","Monitor waste labels and complete them if they are missing any information", "Issue a Waste Pick Up Request with EH&S if Accumulation Date on a label is almost 9 months or if you need to dispose of the waste ASAP", "Version Control and Back Up Code Base on GitHub"]

        reminders = ["🌳 Wear O2 monitor while doing LN2 fill up","🚪 Keep Back Room Door open while doing LN2 fill up","🪤 Don't position yourself such that you are trapped by the dewar","👖 Wear full pants on Lab Maintenance Day", "🚫 Don't reuse gloves", "🦠 Don't touch non-contaminated items with gloves", "🧤 Wear thermal gloves when working with LN2", "🥼🥽 Wear safety coat and goggles", "👥 Use the buddy system if not comfortable doing a task alone"]


        return create_email_content(recipient_name, date_maintenance, instructions, reminders)


    
    def send_lab_maintenance_reminders(self):
        if datetime.today().weekday() == self.maintenance_day:
            tracker = self.load_duty_tracker()
            current_maintenance_id = tracker.get('maintenance', None)
            eligible_members = [member for member in self.lab_members.values() if member['role'] in ['PhD Student', 'Post-Doc']]
            next_maintenance_id = self.get_next_member(eligible_members, current_maintenance_id)

            # Send email reminder
            maintainer_info = next((member for member in eligible_members if member['id'] == next_maintenance_id), {})
            
            # Create email content
            date_maintenance = (date.today() + timedelta(days=1)).isoformat()
            maintenance_message = self.lab_maintance_email(maintainer_info['name'], date_maintenance)

            if maintainer_info:
                subject = "Lab Maintenance Reminder"
                message = maintenance_message
                print(f"Maintenance week by - {maintainer_info['name']}")
                self.email_notifier.send_email([maintainer_info['email']], subject, message)

                # Create a calendar event for the maintenance week
                start_date = (date.today() + timedelta(days=3)).isoformat()  # Start from next Monday
                end_date = (date.today() + timedelta(days=7)).isoformat()    # End on next Friday
                self.calendar_manager.create_event(
                    title=f"Lab Maintenance by {maintainer_info['name']}",
                    description=maintenance_message,
                    start_date=start_date,
                    end_date=end_date,
                    attendees=[maintainer_info['email']],
                    location=self.location,
                    all_day=True
                )

            # Update the duty tracker
            self.update_duty_tracker('maintenance', next_maintenance_id)

    def send_lab_snacks_reminders(self):
        # Send reminders on the day before the presentation including edgecase of sunday
        if datetime.today().weekday() == self.presentation_day - 1 or (datetime.today().weekday() == 6 and self.presentation_day == 0):
            print("Sending lab snacks reminders...")
            tracker = self.load_duty_tracker()
            current_snacks_id = tracker.get('snacks', None)
            eligible_members = [member for member in self.lab_members.values() if member['role'] != 'Undergraduate Student']
            next_snacks_id = self.get_next_member(eligible_members, current_snacks_id)

            # Send email reminder
            snack_person_info = next((member for member in eligible_members if member['id'] == next_snacks_id), {})
            if snack_person_info:
                meeting_date = (date.today() + timedelta(days=1)).strftime("%A, %B %d")
                subject = "Lab Snacks Reminder"
                message = f"Hello {snack_person_info['name']},\n\nThis is a reminder for you to bring snacks for the lab meeting tomorrow ({meeting_date})." + SERVICE_SIGNATURE
                self.email_notifier.send_email([snack_person_info['email']], subject, message)

            print("Snacks bought by - ", snack_person_info['name'])
            # Update the duty tracker
            self.update_duty_tracker('snacks', next_snacks_id)

def alert_developer(e):
    gmail_username = os.environ.get('GMAIL_USERNAME')
    gmail_password = os.environ.get('GMAIL_PASSWORD')
    email_notifier = EmailNotifier(gmail_username, gmail_password)
    token_error_msg = "('invalid_grant: Token has been expired or revoked.', {'error': 'invalid_grant', 'error_description': 'Token has been expired or revoked.'})"
    resolution_msg = f"If error message is\n`{token_error_msg}`\nresoultion is:\n\n1) Delete the `token.pickle` file\n2) Run the script again"
    bar = "=" * 30
    content = f"System Generated Error Message:\n{bar}\n\n{str(e)}\n\nResolutions:\n{bar}\n\n{resolution_msg}"
    email_notifier.send_email([__email__], "Lab Notification System Error", content)

def test_update_duty_tracker(system):
    """Test function to update the duty tracker and push changes."""
    print("Running test to update duty tracker...")

    # Simulate updating the duty tracker
    duty_type = "presentation"
    next_member_id = "test_member_id"
    system.update_duty_tracker(duty_type, next_member_id)

    # Verify the update
    with open('duty_tracker.json', 'r') as file:
        tracker = json.load(file)
    assert tracker[duty_type] == next_member_id
    print("Duty tracker update test passed.")

if __name__ == "__main__":

    presentation_day = os.environ.get('PRESENTATION_DAY')
    presentation_time = os.environ.get('PRESENTATION_TIME')
    maintenance_day = os.environ.get('MAINTENANCE_DAY')
    location = os.environ.get('LOCATION')
    send_presentation_reminders = os.environ.get('SEND_PRESENTATION_REMINDERS', 'false').lower() == 'true'

    system = None
    try:
        system = LabNotificationSystem(presentation_day, presentation_time, maintenance_day, location, send_presentation_reminders)
    except Exception as e:
        print(f"Caught exception during initialization: {e}")
        alert_developer(e)
        sys.exit(1)
    try:
        system.run()
        # Run the test case
        #test_update_duty_tracker(system)
    except Exception as e:
        print(f"Caught exception during execution: {e}")
        alert_developer(e)
        sys.exit(1)
