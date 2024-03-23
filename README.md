# Project Title: Gmail Email Filter and Task Creator

**Description**
This Python project leverages the Gmail API to efficiently process emails from a specific sender (here, vitianscdc2025@vitstudent.ac.in), searching for keywords related to B.Tech CSE registrations, internships, and form links. When found, relevant information is extracted and used to automatically create tasks in Google Tasks, complete with titles and form links in the notes.

**Dependencies**

* Google API Client Library for Python (Install with `pip install google-api-python-client`)
* Beautiful Soup 4 (Install with `pip install beautifulsoup4`)

**Installation**

1. Clone this repository.
2. Install required dependencies: 
   ```bash
   pip install google-api-python-client beautifulsoup4

# Setup and Usage

## Obtain Google API Credentials:

* Follow the instructions to enable the Gmail API and the Tasks API in the Google Cloud Console: Quickstart Guide [https://developers.google.com/gmail/api/quickstart/python](https://developers.google.com/gmail/api/quickstart/python)
* Download your OAuth credentials file as `credentials.json` and place it in the project directory.

## Run the script:
   ```bash
   python gmailfetcher.py

## Explanation

The provided code does the following:

* **Imports necessary libraries:** `pickle`, `base64`, `os.path`, `re`, `email`, `bs4`, and the Google API libraries.
* **`get_gmail_service()`:** Handles authentication and authorization for the Gmail API, providing a service object.
* **`fetch_emails()`:** Queries the Gmail inbox for specific emails, parses them, and filters them based on keywords within the email body.
* **`get_subject()`:** Extracts the email's subject.
* **`get_body()`:** Decodes and extracts the textual content of the email's body.
* **`create_task()`:** Handles authentication and authorization for the Google Tasks API and creates a new task in a specified task list.

