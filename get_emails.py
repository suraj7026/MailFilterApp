import pickle
import base64
import os.path
import re
import email

from bs4 import BeautifulSoup

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/tasks']


def get_gmail_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)



def fetch_emails():
    service = get_gmail_service()

    # Target a specific sender
    now = datetime.utcnow()
    cutoff_time = now - timedelta(hours=6)
    cutoff_str = cutoff_time.isoformat("T") + "Z"

    query = 'from:vitianscdc2025@vitstudent.ac.in (Registration OR Internship OR "2025 Batch") '

    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        # messages = results.get('messages', [])
        messages = results['messages']

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            subject = get_subject(msg['payload']['headers'])
            payload = msg['payload']
            body = get_body(payload)  # Get the body of the email

            print("Subject:", subject)
            print("Body:\n", body)
            print("------")  # Optional separator between emails

    except Exception as e:
        print(f"Error fetching emails: {e}")



def get_body(payload):
    """Extracts and returns the text body from an email part.

    Prioritizes the first decoding method. If decoding fails, attempts the second method.

    Args:
        payload: An email part object (e.g., from an email.message object)

    Returns:
        str: The decoded text body, or an error message if decoding fails with both methods.
    """

    # First decoding method
    try:
        message_parts = payload['parts']
        part = message_parts[0]
        part_body = part['body']
        part_data = part_body['data']
        clean_data = part_data.replace("-", "+").replace("_", "/")
        clean_body = base64.b64decode(bytes(clean_data, 'UTF-8'))
        soup = BeautifulSoup(clean_body, "lxml")
        message_body = soup.body()
        return str(message_body)  # Success!

    except Exception as e:
        # First method failed, try the second
        try:
            message_parts = payload['parts'][0]['parts']
            part = message_parts[0]
            part_body = part['body']
            part_data = part_body['data']
            clean_data = part_data.replace("-", "+").replace("_", "/")
            clean_body = base64.b64decode(bytes(clean_data, 'UTF-8'))
            soup = BeautifulSoup(clean_body, "lxml")
            message_body = soup.body()
            return str(message_body)  # Success with second method

        except Exception as e:
            return f"Error decoding message (both methods failed): {e}"





    """
    message_main_type = part.get_content_maintype()
    if message_main_type == 'multipart':
        for subpart in part.get_payload():
            if subpart.get_content_maintype() == 'text':
                return subpart.get_payload(decode=True).decode('utf-8')  # Decode directly
    elif message_main_type == 'text':
        return part.get_payload(decode=True).decode('utf-8')  # Decode directly

    return ''  # No text body found
    """



def get_subject(headers):
    for header in headers:
        if header.get('name') == 'Subject':
            return header.get('value')
    return ""

if __name__ == '__main__':
    fetch_emails()
