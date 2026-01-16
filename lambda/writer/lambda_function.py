import json
import boto3
import os
import re
import time
import uuid
from datetime import datetime

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
MAX_NAME_LEN = 100
MAX_SUBJECT_LEN = 150
MAX_MESSAGE_LEN = 2000

def resp(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body)
    }

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))

        name = (body.get("name") or "").strip()
        email = (body.get("email") or "").strip()
        subject = (body.get("subject") or "Contact Form Submission").strip()
        message = (body.get("message") or "").strip()

        # Optional anti-bot honeypot (frontend may send hidden field "website")
        honeypot = (body.get("website") or "").strip()
        if honeypot:
            return resp(400, {"error": "Spam detected."})

        # Validation
        if not name or not email or not message:
            return resp(400, {"error": "Name, email, and message are required."})
        if len(name) > MAX_NAME_LEN:
            return resp(400, {"error": f"Name is too long (max {MAX_NAME_LEN})."})
        if len(subject) > MAX_SUBJECT_LEN:
            return resp(400, {"error": f"Subject is too long (max {MAX_SUBJECT_LEN})."})
        if len(message) > MAX_MESSAGE_LEN:
            return resp(400, {"error": f"Message is too long (max {MAX_MESSAGE_LEN})."})
        if not EMAIL_RE.match(email):
            return resp(400, {"error": "Email format looks invalid."})

        sender_email = os.environ["SENDER_EMAIL"]
        table_name = os.environ["TABLE_NAME"]

        created_at_ms = int(time.time() * 1000)
        submission_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        email_body = f"""
New Contact Form Submission

Time: {timestamp}
Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
""".strip()

        # 1) Send email (SESv2)
        sesv2 = boto3.client("sesv2", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        send_resp = sesv2.send_email(
            FromEmailAddress=f"Contact Form <{sender_email}>",
            ReplyToAddresses=[email],
            Destination={"ToAddresses": [sender_email]},
            Content={
                "Simple": {
                    "Subject": {"Data": f"📩 Website message — {name}: {subject}"},
                    "Body": {"Text": {"Data": email_body}}
                }
            }
        )

        # 2) Save submission (DynamoDB)
        ddb = boto3.resource("dynamodb")
        table = ddb.Table(table_name)
        table.put_item(
            Item={
                "pk": "SUBMISSION",
                "createdAt": created_at_ms,
                "submissionId": submission_id,
                "name": name,
                "email": email,
                "subject": subject,
                "message": message,
                "userAgent": (event.get("headers") or {}).get("User-Agent", ""),
                "sourceIp": (((event.get("requestContext") or {}).get("identity") or {}).get("sourceIp")) or ""
            }
        )

        return resp(200, {"message": "Email sent and submission saved.", "messageId": send_resp.get("MessageId", ""), "submissionId": submission_id})

    except Exception as e:
        print(f"Error: {str(e)}")
        return resp(500, {"error": "Internal server error"})
