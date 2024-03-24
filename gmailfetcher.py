import pickle
import base64
import os.path
import re
import datetime
import datefinder
from dateutil import parser
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

    """
    Authenticates with Gmail and builds a service object for API interactions.

    This function handles the following:

        * Checks for existing valid credentials in a 'token.pickle' file.
        * Refreshes credentials if expired and a refresh token is available.
        * Initiates an OAuth 2.0 authorization flow if credentials are not found or invalid.
        * Stores the obtained credentials in 'token.pickle' for future use.

    Returns:
        build.Service: A Gmail API v1 service object ready for making requests.
    """

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


def create_task(task_title, form_link, due_date=None):

    """
    Creates a new task in a Google Tasks list.

    Args:
        task_title (str): The title of the task.
        form_link (str): An optional link to a related form.
        due_date (datetime.date, optional): The due date for the task. Defaults to None.

    Raises:
        HttpError: If an error occurs during the Google Tasks API interaction.
    """

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("tasks", "v1", credentials=creds)

        # Call the Tasks API
        results = service.tasklists().list(maxResults=10).execute()
        items = results.get("items", [])

        task_id = 'MDY2NjE1NTc2ODE1NjI2NDM1Mzg6MDow'  # Replace with the correct ID

        # Call the Tasks API to get the tasks in the first task list
        tasks = service.tasks().list(tasklist=task_id).execute()
        task_items = tasks.get('items', [])

        """"
        if not task_items:
            print('No tasks found in the first task list.')
        else:
            print('Tasks in the first task list:')
            for task in task_items:
                print(f'{task["title"]} ({task["id"]})')
        """

        # Insert a new task into the first task list

        new_task = {
            'title': f'{task_title}',
            'notes': f'{form_link}'
        }

        if due_date != None:
            new_task['due'] = f'{due_date}'

        # print(new_task)

        inserted_task = service.tasks().insert(tasklist=task_id, body=new_task).execute()
        print(f"New task inserted: {inserted_task['title']} ({inserted_task['id']})")

    except HttpError as err:
        print("Unable to Find Due Date")


def find_registration_date(text):
    """
    Finds the last registration date within a block of text, handling
    various date formats.

    Args:
        text: The input text block.

    Returns:
        The registration date as a string (YYYY-MM-DD format), or None if no date is found.
    """

    # date_patterns = [
    #     r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
    #     r"\d{2}(st|nd|rd|th)\s+(January|February|March|April|May|June|July|August|September|October|November|December)(,|)\s+\d{4}"  # DDth Month, YYYY
    #     # Add more patterns as needed...
    # ]

    # search_phrases = [r"on or before"]

    # for pattern in date_patterns:
    #     for phrase in search_phrases:
    #         matches = re.findall(rf"{phrase}\s+({pattern})", text, re.IGNORECASE)
    #         # print(matches)
    #         if matches:
    #             if isinstance(matches[-1],tuple):
    #                 return normalize_date(matches[-1][0])

    #             return normalize_date(matches[-1])  # Return the last found date in YYYY-MM-DD

    # return None  # No date found

    matches = list(datefinder.find_dates(text,strict = True))

    return normalize_date(matches[-1])


def normalize_date(date_str):
        """
        Converts a date string from various formats to YYYY-MM-DDTHH:mm:ssZ
        """

        return date_str.isoformat() + 'Z'



def fetch_emails():

    """
    Fetches relevant emails from Gmail and creates Google Tasks with extracted information.

    This function searches for emails containing specific keywords related to registration,
    internships, or the "2025 Batch" from a specific sender. For each matching email, it extracts
    the following details:

        - Subject
        - Form link (if present)
        - Due date (if present; otherwise, the task is created without a due date)

    It then creates a Google Task with this information.

    Raises:
        Exception: If any errors occur during the process.
    """

    service = get_gmail_service()

    # Calculate cutoff time
    now = datetime.utcnow()
    cutoff_time = now - timedelta(hours=6)
    cutoff_str = cutoff_time.isoformat("T") + "Z"

    # query = f'from:vitianscdc2025@vitstudent.ac.in (Registration OR Internship OR "2025 Batch") after:{cutoff_str}'
    query = 'from:vitianscdc2025@vitstudent.ac.in (Registration OR Internship OR "2025 Batch")'
    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg['payload']


            body = get_body(payload)

            if body and re.search(r'\bB\.?\s*Tech\b', body, re.IGNORECASE):
                subject = get_subject(msg['payload']['headers'])
                link = re.search(r'https://forms\.gle/(\S+)', body)
                due_date = find_registration_date(body)

                if link:
                    create_task(subject, link.group(0), due_date)  # Pass due_date, might be None
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
            try:
                message_parts = payload['parts'][0]['parts'][0]['parts']
                part = message_parts[0]
                part_body = part['body']
                part_data = part_body['data']
                clean_data = part_data.replace("-", "+").replace("_", "/")
                clean_body = base64.b64decode(bytes(clean_data, 'UTF-8'))
                soup = BeautifulSoup(clean_body, "lxml")
                message_body = soup.body()
                return str(message_body)  # Success with third method
            except Exception as e:
                return f"Error decoding message (Three methods failed): {e}"


def get_subject(headers):
    for header in headers:
        if header.get('name') == 'Subject':
            return header.get('value')
    return ""

if __name__ == '__main__':
    fetch_emails()
