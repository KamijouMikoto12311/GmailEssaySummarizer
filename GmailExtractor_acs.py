import os
import base64
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None

    token_path = "./config/token.json"
    credentials_path = "./config/credentials.json"

    # Load credentials if they exist
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If credentials are invalid, reauthenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _extract_body_from_payload(payload):
    """Extract the body from the payload"""
    if "body" in payload:
        body_data = payload["body"].get("data", "")
        if body_data:
            body = body_data.replace("-", "+").replace("_", "/")  # Decode base64url encoding
            return base64.urlsafe_b64decode(body).decode("utf-8")
    return None


def _write_email_to_file(subject, timestamp, links, filename="./data/acs_email_links.txt"):
    """Write email subject, timestamp, and filtered links to a file"""
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"📜 Subject: {subject}\n")
        file.write(f"🕒 Time: {timestamp}\n")
        if links:
            file.write("🔗 Found 'Read Article' Links:\n")
            for link in links:
                file.write(f"{link}\n")
        else:
            file.write("❌ No matching links found.\n")
        file.write("\n")


def check_gmail(max_num=6):

    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

    service = _get_gmail_service()
    print("✅ Connected to Gmail API!")

    query = "is:unread from:journalalerts@acs.org"
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q=query, maxResults=max_num).execute()
    print("✅ Fetched message IDs from Gmail!")

    messages = results.get("messages", [])
    if not messages:
        print("❌ No new emails found.")
        return
    print(f"📩 Found {len(messages)} emails from journalalerts@acs.org:")

    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = msg_data["payload"]["headers"]

        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")

        date_header = next((h["value"] for h in headers if h["name"] == "Date"), None)
        if date_header:
            timestamp = parsedate_to_datetime(date_header)
        else:
            timestamp = "Unknown Time"

        body = _extract_body_from_payload(msg_data["payload"])

        filtered_links = []
        if body:
            soup = BeautifulSoup(body, "html.parser")

            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"]
                # Check if the link contains 'Read Article' text and the specific URL structure
                if re.search(r"\bRead Article\b", link.get_text(), re.IGNORECASE):
                    filtered_links.append(href)

        _write_email_to_file(subject, timestamp, filtered_links)

    os.environ["HTTP_PROXY"] = ""
    os.environ["HTTPS_PROXY"] = ""


if __name__ == "__main__":
    with open("./data/email_links.txt", "w") as f:
        f.write("")
    check_gmail()
