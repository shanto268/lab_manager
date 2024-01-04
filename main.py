import os
import json
import subprocess
import holidays

from datetime import date, datetime
from config_loader import ConfigLoader
from email_notifier import EmailNotifier
from slack_notifier import SlackNotifier
from calendar_manager import CalendarManager

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


class LabNotificationSystem:
    def __init__(self, presentation_day, presentation_time, presentation_message, maintenance_message, snacks_message):
        self.lab_members = ConfigLoader('lab_members.json').load_config()
        self.gmail_username = os.environ.get('GMAIL_USERNAME')
        self.gmail_password = os.environ.get('GMAIL_PASSWORD')
        self.slack_token = os.environ.get('SLACK_TOKEN')
        self.google_calendar_service_key = json.loads(os.environ.get('GOOGLE_CALENDAR_SERVICE_KEY'))

        self.presentation_day = chosen_day(presentation_day)
        self.presentation_time = presentation_time
        self.presentation_message = presentation_message
        self.maintenance_message = maintenance_message
        self.snacks_message = snacks_message
        self.us_holidays = holidays.US()


        self.email_notifier = EmailNotifier(self.gmail_username, self.gmail_password)
        self.calendar_manager = CalendarManager(self.google_calendar_service_key, self.email_notifier)
        self.slack_notifier = SlackNotifier(self.slack_token)

    def run(self):
        self.send_presentation_reminders()
        self.send_lab_maintenance_reminders()
        self.send_lab_snacks_reminders()

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
        self.commit_and_push_changes()

    def commit_and_push_changes(self):
        subprocess.run(['git', 'add', 'duty_tracker.json'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Update duty tracker'], check=True)
        subprocess.run(['git', 'push'], check=True)

    def no_meeting(self, today):
        # Check if today is a national holiday
        if today in self.us_holidays:
            self.slack_notifier.send_message('#test-gpt', f"Reminder: No lab meeting today due to a national holiday - {self.us_holidays.get(today)}")
            return True
        # Check if today is the first presentation day of the month
        elif today.day == self.presentation_day:
            self.slack_notifier.send_message('#test-gpt', "Reminder: Today is 'Lab Citizen Day'")
            return True
        # All else case
        else:
            return False

    def send_presentation_reminders(self):
        today = datetime.today()
        tracker = self.load_duty_tracker()

        if today.weekday() == self.presentation_day:  
            if self.no_meeting(today):
                pass
            else:
                current_presenter_id = tracker.get('presentation', None)
                next_presenter_id, is_group_presentation = self.get_next_presenter(current_presenter_id)

                # Send email to the next presenter
                presenter_info = next((member for member in self.lab_members if member['id'] == next_presenter_id), {})
                if presenter_info:
                    subject = "Your Turn to Present at Next Week's Lab Meeting"
                    message = f"Hello {presenter_info['name']},\n\nYou are scheduled to present at next week's lab meeting."
                    self.email_notifier.send_email([presenter_info['email']], subject, message)

                # Send Slack notification
                if is_group_presentation:
                    message = "This week's presentation will be given by our undergraduate students."
                else:
                    message = f"This week's presentation will be given by {presenter_info['name']}."
                self.slack_notifier.send_message('#test-gpt', message)

                # Update the duty tracker
                self.update_duty_tracker('presentation', next_presenter_id)

    def load_duty_tracker(self):
        with open('duty_tracker.json', 'r') as file:
            return json.load(file)

    def get_next_presenter(self, current_presenter_id):
        # Assuming undergrads are grouped and present together
        undergrads = [member for member in self.lab_members if member['role'] == 'Undergraduate Student']
        non_undergrads = [member for member in self.lab_members if member['role'] != 'Undergraduate Student']

        if current_presenter_id in [u['id'] for u in undergrads]:
            next_presenter_id = non_undergrads[0]['id']
            return next_presenter_id, False
        elif current_presenter_id in [n['id'] for n in non_undergrads]:
            index = non_undergrads.index(next((n for n in non_undergrads if n['id'] == current_presenter_id), None))
            next_index = (index + 1) % len(non_undergrads)
            next_presenter_id = non_undergrads[next_index]['id']
            return next_presenter_id, False
        else:
            # If no current presenter or cycle restarts, start with undergrads
            return undergrads[0]['id'], True

    def send_lab_maintenance_reminders(self):
        if datetime.today().weekday() == 4:  # Friday
            tracker = self.load_duty_tracker()
            current_maintenance_id = tracker.get('maintenance', None)
            eligible_members = [member for member in self.lab_members if member['role'] in ['PhD Student', 'Post-Doc']]
            next_maintenance_id = self.get_next_member(eligible_members, current_maintenance_id)

            # Send email reminder
            maintainer_info = next((member for member in eligible_members if member['id'] == next_maintenance_id), {})
            if maintainer_info:
                subject = "Lab Maintenance Duty Reminder"
                message = f"Hello {maintainer_info['name']},\n\nThis is a reminder that you are on lab maintenance duty next week."
                self.email_notifier.send_email([maintainer_info['email']], subject, message)

                # Create a calendar event for the maintenance week
                start_date = (date.today() + timedelta(days=3)).isoformat()  # Start from next Monday
                end_date = (date.today() + timedelta(days=7)).isoformat()    # End on next Friday
                self.calendar_manager.create_event(
                    title="Lab Maintenance Duty",
                    start_date=start_date,
                    end_date=end_date,
                    attendees=[maintainer_info['email']]
                )

            # Update the duty tracker
            self.update_duty_tracker('maintenance', next_maintenance_id)

    def send_lab_snacks_reminders(self):
        presentation_day = "Wednesday"  # Adjust as needed
        if datetime.today().weekday() == chosen_day(presentation_day) - 1:
            tracker = self.load_duty_tracker()
            current_snacks_id = tracker.get('snacks', None)
            eligible_members = [member for member in self.lab_members if member['role'] != 'Undergraduate Student']
            next_snacks_id = self.get_next_member(eligible_members, current_snacks_id)

            # Send email reminder
            snack_person_info = next((member for member in eligible_members if member['id'] == next_snacks_id), {})
            if snack_person_info:
                subject = "Lab Snacks Reminder"
                message = f"Hello {snack_person_info['name']},\n\nThis is a reminder for you to bring snacks for the lab meeting on {presentation_day}."
                self.email_notifier.send_email([snack_person_info['email']], subject, message)

            # Update the duty tracker
            self.update_duty_tracker('snacks', next_snacks_id)

if __name__ == "__main__":
    presentation_day = "Wednesday"
    presentation_time = "2:00 PM"
    presentation_message = "This week's presentation will be given by {presenter_name}."
    maintenance_message = "This is a reminder that you are on lab maintenance duty next week."
    snacks_message = "This is a reminder for you to bring snacks for the lab meeting on {presentation_day}."

    system = LabNotificationSystem(presentation_day, presentation_time, presentation_message, maintenance_message, snacks_message)
    system.run()
