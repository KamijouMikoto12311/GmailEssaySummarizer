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
    """
    Authenticate and return a Gmail API service instance.
    Uses local token.json if valid; otherwise uses credentials.json to create a new token.
    """
    creds = None
    token_path = "./config/token.json"
    credentials_path = "./config/credentials.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _extract_parts(payload):
    """
    Recursively traverse the payload to find all parts that contain 'data'.
    Yields tuples of (mime_type, base64url_encoded_data).
    """
    if "parts" in payload:
        for part in payload["parts"]:
            yield from _extract_parts(part)
    else:
        body_data = payload.get("body", {}).get("data")
        mime_type = payload.get("mimeType", "")
        if body_data:
            yield (mime_type, body_data)


def _decode_base64url(encoded_str):
    """
    Decode a Base64URL-encoded string (as used by Gmail) into a UTF-8 string.
    """
    encoded_str = encoded_str.replace("-", "+").replace("_", "/")
    decoded_bytes = base64.urlsafe_b64decode(encoded_str)
    return decoded_bytes.decode("utf-8")


def _extract_message_body(payload):
    """
    Extract the first HTML or plain-text body found in the message payload.
    If both exist, prefer the HTML body.
    Returns a string (the email content) or None if not found.
    """
    parts_found = list(_extract_parts(payload))
    text_body = None
    html_body = None

    for mime_type, data_str in parts_found:
        decoded_content = _decode_base64url(data_str)
        if mime_type == "text/plain" and text_body is None:
            text_body = decoded_content
        elif mime_type == "text/html" and html_body is None:
            html_body = decoded_content

    return html_body if html_body else text_body


def _write_email_to_file(subject, timestamp, links, filename="./data/aps_email_links.txt"):
    """
    Write email subject, timestamp, and filtered links to a file (append mode).
    """
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"📜 Subject: {subject}\n")
        file.write(f"🕒 Time: {timestamp}\n")
        if links:
            file.write("🔗 Found Links:\n")
            for link in links:
                file.write(f"{link}\n")
        else:
            file.write("❌ No matching links found.\n")
        file.write("\n")


def check_gmail(max_num=6):
    """
    Connect to Gmail API, query unread emails from journals-comm@aps.org,
    extract subject, timestamp, and links from the email body, then append the results
    to ./data/aps_email_links.txt.
    """
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

    service = _get_gmail_service()
    print("✅ Connected to Gmail API!")

    query = "is:unread from:journals-comm@aps.org"
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q=query, maxResults=max_num).execute()
    print("✅ Fetched message IDs from Gmail!")

    messages = results.get("messages", [])
    if not messages:
        print("❌ No new emails found.")
        return

    print(f"📩 Found {len(messages)} emails from journals-comm@aps.org:")

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

        body = _extract_message_body(msg_data["payload"])
        filtered_links = []

        if body:
            soup = BeautifulSoup(body, "html.parser")
            letters_elements = soup.find_all(string=re.compile("LETTERS"))
            if letters_elements:
                last_letters = letters_elements[-1]
                marker = last_letters.parent
                links_after_marker = marker.find_all_next("a", href=True)
                for link in links_after_marker:
                    href = link["href"]
                    if "m-email-utm-campaign-prl-alert" in href:
                        filtered_links.append(href)
            else:
                print("⚠️ 'LETTERS' marker not found in the email body.")

        _write_email_to_file(subject, timestamp, filtered_links)

    os.environ["HTTP_PROXY"] = ""
    os.environ["HTTPS_PROXY"] = ""


if __name__ == "__main__":
    with open("./data/aps_email_links.txt", "w", encoding="utf-8") as f:
        f.write("")
    check_gmail()
