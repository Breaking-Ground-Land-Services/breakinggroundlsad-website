#!/usr/bin/env python3
"""Email Breaking Ground the Formspree claim link to activate website estimate forms."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EMAIL_AGENT = Path(r"C:\Users\nknig\Downloads\GPTStudy\Email-Agent")
ENV_FILE = EMAIL_AGENT / ".env"

FROM_EMAIL = "support@knightlogics.com"
TO_EMAIL = "contact@breakinggroundlsad.com"
FORM_NAME = "Breaking Ground Estimate Request"
PROJECT = "breakinggroundlsad-website"

CLAIM_URL = (
    "https://formspree.io/claim?"
    + urllib.parse.urlencode(
        {
            "name": FORM_NAME,
            "project": PROJECT,
            "field.name": "text,required,prettyName:Name",
            "field.phone": "text,required,prettyName:Phone",
            "field.email": "email",
            "field.job_location": "text,required,prettyName:Job location",
            "field.service": "text,required,prettyName:Service needed",
            "field.message": "text,prettyName:Project details",
            "field.can_text_photos": "text,prettyName:Can we text for photos",
            "field.best_time": "text,prettyName:Best time to call",
            "field.photos": "file",
            "field.page": "text",
            "action.email": TO_EMAIL,
        },
        quote_via=urllib.parse.quote,
    )
)

ZOHO_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
ZOHO_API_BASE = "https://mail.zoho.com/api"


def load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.is_file():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def zoho_access_token(env: dict[str, str]) -> str:
    params = urllib.parse.urlencode(
        {
            "refresh_token": env["EMAIL_AGENT_ZOHO_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
            "client_id": env["EMAIL_AGENT_ZOHO_CLIENT_ID"],
            "client_secret": env["EMAIL_AGENT_ZOHO_CLIENT_SECRET"],
        }
    ).encode("utf-8")
    req = urllib.request.Request(ZOHO_TOKEN_URL, data=params, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Zoho token exchange failed: {data}")
    return token


def zoho_account_id(access_token: str, email: str) -> str:
    req = urllib.request.Request(f"{ZOHO_API_BASE}/accounts")
    req.add_header("Authorization", f"Zoho-oauthtoken {access_token}")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for account in data.get("data", []):
        if account.get("primaryEmailAddress", "").lower() == email.lower():
            return str(account["accountId"])
    if data.get("data"):
        return str(data["data"][0]["accountId"])
    raise RuntimeError(f"No Zoho account found for {email}")


def build_email_body() -> str:
    today = date.today().strftime("%B %d, %Y")
    return f"""Hi Guy and Andrew,

Your website estimate forms at https://breakinggroundlsad.com are already wired to send submissions to {TO_EMAIL}. The last step is activating Formspree so those submissions actually arrive in your inbox.

STEP 1 — Activate Formspree (about 2 minutes)
Open this link and sign up or log in with {TO_EMAIL}:

{CLAIM_URL}

Formspree will create a form named "{FORM_NAME}" and route every website submission to {TO_EMAIL}.

STEP 2 — Test the form
After activation, visit https://breakinggroundlsad.com/contact/ and submit a quick test estimate. You should receive the notification at {TO_EMAIL} within a minute or two.

STEP 3 — Reply with your form endpoint (optional but helpful)
After claiming the form, Formspree shows an endpoint like:
https://formspree.io/f/xxxxxxxx

Reply to this email with that URL and we will lock it into the site build so forms stay active long-term.

Where forms appear on the site:
• Homepage and contact page
• Every service page (demolition, land clearing, tree removal, etc.)
• All 50 local service area pages

If you do not see a Formspree email after clicking the link, check spam/junk and add formspree.io to your safe senders list.

Questions? Reply here or call/text Nicholas at Knight Logics.

Best regards,
Nicholas Knight
Knight Logics
support@knightlogics.com
https://knightlogics.com

Prepared {today}
"""


def zoho_send_email(
    access_token: str,
    account_id: str,
    *,
    to_email: str,
    subject: str,
    body: str,
) -> dict:
    payload = {
        "fromAddress": FROM_EMAIL,
        "toAddress": to_email,
        "subject": subject,
        "content": body,
        "mailFormat": "plaintext",
    }
    encoded = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{ZOHO_API_BASE}/accounts/{account_id}/messages",
        data=encoded,
        method="POST",
    )
    req.add_header("Authorization", f"Zoho-oauthtoken {access_token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    env = load_env(ENV_FILE)
    required = [
        "EMAIL_AGENT_ZOHO_CLIENT_ID",
        "EMAIL_AGENT_ZOHO_CLIENT_SECRET",
        "EMAIL_AGENT_ZOHO_REFRESH_TOKEN",
    ]
    missing = [k for k in required if not env.get(k)]
    if missing:
        raise SystemExit(f"Missing Zoho env keys in {ENV_FILE}: {', '.join(missing)}")

    subject = "Action needed: activate website estimate forms (Formspree)"
    body = build_email_body()

    token = zoho_access_token(env)
    account_id = zoho_account_id(token, FROM_EMAIL)
    result = zoho_send_email(
        token,
        account_id,
        to_email=TO_EMAIL,
        subject=subject,
        body=body,
    )
    print(f"Claim URL:\n{CLAIM_URL}\n")
    print(f"Sent email from {FROM_EMAIL} to {TO_EMAIL}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {err}", file=sys.stderr)
        raise SystemExit(1) from exc
