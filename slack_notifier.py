import requests

class SlackNotifier:
    def __init__(self, token):
        self.token = token

    def send_message(self, channel, message):
        """Send a message to a Slack channel."""
        url = 'https://slack.com/api/chat.postMessage'
        headers = {'Authorization': f'Bearer {self.token}'}
        payload = {'channel': channel, 'text': message}

        response = requests.post(url, headers=headers, data=payload)
        if not response.json().get("ok"):
            raise Exception(f"Error sending message to Slack: {response.json()}")
