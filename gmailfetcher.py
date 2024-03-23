import pickle
import base64
import os.path
import re
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

def create_task(task_title,form_link):
  """Shows basic usage of the Tasks API.
  Prints the title and ID of the first 10 task lists.
  """
  creds = None

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("tasks", "v1", credentials=creds)

    # Call the Tasks API
    results = service.tasklists().list(maxResults=10).execute()
    items = results.get("items", [])


    task_id = 'MDY2NjE1NTc2ODE1NjI2NDM1Mzg6MDow'

    # Call the Tasks API to get the tasks in the first task list
    tasks = service.tasks().list(tasklist=task_id).execute()
    task_items = tasks.get('items', [])

    if not task_items:
        print('No tasks found in the first task list.')
    else:
        print('Tasks in the first task list:')
        for task in task_items:
            print(f'{task["title"]} ({task["id"]})')

    # Insert a new task into the first task list
    new_task = {
        'title': f'{task_title}',
        'notes': f'{form_link}',
    }
    inserted_task = service.tasks().insert(tasklist=task_id, body=new_task).execute()
    print(f"New task inserted: {inserted_task['title']} ({inserted_task['id']})")

  except HttpError as err:
    print(err)

def fetch_emails():
    service = get_gmail_service()

    # Calculate cutoff time
    now = datetime.utcnow()
    cutoff_time = now - timedelta(hours=6)
    cutoff_str = cutoff_time.isoformat("T") + "Z"

    query = 'from:vitianscdc2025@vitstudent.ac.in (Registration OR Internship OR "2025 Batch") after:{}'.format(cutoff_str)
    # query = 'from:vitianscdc2025@vitstudent.ac.in (Registration OR Internship OR "2025 Batch")'
    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg['payload']

            # Search in text parts
            # if payload.get('mimeType') == 'text/plain':
            #     body = get_body(payload)
            # elif payload.get('mimeType') == 'multipart/alternative':
            #     for part in payload.get('parts'):
            #         if part.get('mimeType') == 'text/plain':
            #             body = get_body(part)
            #             break
            # else:
            #     continue
            body = get_body(payload)

            if body and re.search(r'\bB\.?\s*Tech\b', body, re.IGNORECASE):
                subject = get_subject(msg['payload']['headers'])
                link = re.search(r'https://forms.gle/(\S+)', body)
                if link:
                    create_task(subject, link.group(0))
            # subject = get_subject(msg['payload']['headers'])
            # body = get_body(msg['payload'])  # Get the body of the email

            # print("Subject:", subject)
            # print("Body:\n", body)
            # print("------")

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



# def get_body(part):
#     if part.get('body').get('data'):
#         try:
#             data = part['body']['data']
#             data = data.replace("-", "+").replace("_", "/")
#             decoded_data = base64.urlsafe_b64encodes(data)
#             soup = BeautifulSoup(decoded_data, "lxml")
#             body = soup.body()
#             return str(body)  # Convert to string for consistent output
#         except:
#             return "Error decoding email body"
#     else:
#         return ""


def get_subject(headers):
    for header in headers:
        if header.get('name') == 'Subject':
            return header.get('value')
    return ""

if __name__ == '__main__':
    fetch_emails()
