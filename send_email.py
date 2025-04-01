import os
import smtplib
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Get authenticated Gmail API service."""
    creds = None
    token_path = 'token.json'  # Path in the root directory
    credentials_path = 'credentials.json'  # Path in the root directory
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_info(json.load(open(token_path)))
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def check_email_read_status():
    """Check if the most recent email has been read."""
    try:
        service = get_gmail_service()
        
        # Get the most recent email with the subject containing "Update Report"
        results = service.users().messages().list(
            userId='me',
            q='subject:"Update Report"'
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print("No emails found.")
            return False
        
        # Get the most recent message
        msg = service.users().messages().get(
            userId='me', 
            id=messages[0]['id']
        ).execute()
        
        # Check if the email has been read (no UNREAD label)
        labels = msg['labelIds']
        return 'UNREAD' not in labels
        
    except Exception as e:
        print(f"Error checking email status: {e}")
        # Default to false if we can't check the email status
        return False

def send_email_with_attachment(subject, sender_email, receiver_email, password, email_body, attachment_path=None):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(email_body, 'html'))

    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
            msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()
