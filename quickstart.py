import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Combined SCOPES for both Tasks and Gmail
SCOPES = [
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/gmail.readonly"
]

# Unified main function
def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Build both Tasks and Gmail services
        tasks_service = build("tasks", "v1", credentials=creds)
        gmail_service = build("gmail", "v1", credentials=creds)

        # Call Tasks API
        print("Task Lists:")
        results = tasks_service.tasklists().list(maxResults=10).execute()
        items = results.get("items", [])
        for item in items:
            print(f"{item['title']} ({item['id']})")

        # Call Gmail API
        print("\nGmail Labels:")
        results = gmail_service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        for label in labels:
            print(label["name"])

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
