from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize the Slack client with your bot token
client = WebClient(token="YOUR_SLACK_BOT_TOKEN")

try:
    # Send message to Harsh
    response = client.chat_postMessage(
        channel="@harsh",  # Replace with Harsh's Slack member ID or username
        text="HI HARSH"
    )
    print("Message sent successfully!")
    
except SlackApiError as e:
    print(f"Error sending message: {e.response['error']}") 