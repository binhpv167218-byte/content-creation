"""
Email Classifier — Pattern-matching classifier for Gmail emails.

Usage:
    python3 scripts/classify-emails.py <input_file> [--output <output_file>]

Input: Text file with email data in Gmail search format (ID/Subject/From/Date blocks)
       OR JSON file from MCP tool result (array with text field)

Output: JSON with emails grouped by label ID, plus summary stats.

Example:
    python3 scripts/classify-emails.py emails.txt
    python3 scripts/classify-emails.py tool-result.txt --output classified.json
"""

import json
import re
import sys
from pathlib import Path


# ─── Classification Rules ───────────────────────────────────────────────────

SECURITY_SENDERS = [
    "no-reply@accounts.google.com",
    "security@facebookmail.com",
    "support.facebook.com",
]

SECURITY_GITHUB_SENDER = "no-reply@github.com"
SECURITY_GITHUB_KEYWORDS = ["policy", "update", "permissions"]

ORDERS_SENDER = "notification@ladipage.net"

SKOOL_SENDER = "noreply@skool.com"

AI_NEWSLETTER_DOMAINS = [
    "substack.com",
    "beehiiv.com",
    "tldrnewsletter.com",
    "therundown.ai",
    "daily.therundown.ai",
    "learn.therundown.ai",
    "joinsuperhuman.ai",
    "practicaly.ai",
    "neatprompts.com",
    "theneurondaily.com",
    "deeplearning.ai",
    "every.to",
    "mail.notion.so",
    "liamottley.com",
    "aiblackmagic.com",
    "earlyaidopterscommunity.com",
    "email.claude.com",
]

# Sender domains that are always Promotions even if they match newsletter patterns
PROMOTIONS_OVERRIDE_SENDERS = [
    "promotions@technologyreview.com",
    "notify@mail.notion.so",
    "billing@mail.notion.so",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def extract_email_address(from_field: str) -> str:
    """Extract email address from From field like '"Name" <email@domain.com>'."""
    match = re.search(r"<([^>]+)>", from_field)
    if match:
        return match.group(1).lower()
    return from_field.strip().lower()


def get_domain(email_address: str) -> str:
    """Get domain from email address."""
    parts = email_address.split("@")
    return parts[1] if len(parts) == 2 else ""


def matches_domain(email_address: str, domains: list[str]) -> bool:
    """Check if email address matches any of the given domains (including subdomains)."""
    domain = get_domain(email_address)
    for d in domains:
        if domain == d or domain.endswith("." + d):
            return True
    return False


def classify_email(email_address: str, subject: str, from_field: str) -> str:
    """
    Classify a single email. Returns label ID (Label_1 through Label_7).
    Priority order: Security > Orders > Skool/Revenue > Skool/Message > Skool/Digest > AI Newsletter > Promotions
    """
    subject_lower = subject.lower()

    # 1. Security — highest priority
    for sender in SECURITY_SENDERS:
        if sender in email_address or sender in from_field.lower():
            return "Label_7"

    if SECURITY_GITHUB_SENDER in email_address:
        if any(kw in subject_lower for kw in SECURITY_GITHUB_KEYWORDS):
            return "Label_7"

    if "security@facebookmail.com" in from_field.lower():
        return "Label_7"

    # 2. Orders
    if ORDERS_SENDER in email_address:
        return "Label_5"

    # 3-5. Skool patterns
    if SKOOL_SENDER in email_address:
        if subject_lower.startswith("new customer:") or subject_lower.startswith("member upgrade:"):
            return "Label_2"  # Revenue
        if "sent you a message" in subject_lower:
            return "Label_3"  # Message
        if "posted" in subject_lower:
            return "Label_4"  # Digest (community posts)
        if any(kw in subject_lower for kw in ["weekly digest", "notification since", "event happening"]):
            return "Label_4"  # Digest
        # Unknown Skool pattern → Digest as fallback
        return "Label_4"

    # 6. AI Newsletter — check sender domain
    # First exclude known promotions senders
    if email_address not in [s.lower() for s in PROMOTIONS_OVERRIDE_SENDERS]:
        if matches_domain(email_address, AI_NEWSLETTER_DOMAINS):
            return "Label_1"

    # Substack digests (from no-reply@substack.com) → Skool/Digest
    if "no-reply@substack.com" in email_address:
        return "Label_4"

    # 7. Promotions — everything else
    return "Label_6"


# ─── Parsing ─────────────────────────────────────────────────────────────────

def parse_gmail_text(text: str) -> list[dict]:
    """Parse Gmail search output (ID/Subject/From/Date blocks) into email dicts."""
    emails = []
    current = {}

    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("ID: "):
            if current and "id" in current:
                emails.append(current)
            current = {"id": line[4:].strip()}
        elif line.startswith("Subject: "):
            current["subject"] = line[9:].strip()
        elif line.startswith("From: "):
            current["from"] = line[6:].strip()
        elif line.startswith("Date: "):
            current["date"] = line[6:].strip()

    if current and "id" in current:
        emails.append(current)

    return emails


def load_input(filepath: str) -> list[dict]:
    """Load emails from input file (plain text or JSON MCP result)."""
    path = Path(filepath)
    content = path.read_text(encoding="utf-8", errors="replace")

    # Try JSON first (MCP tool result format)
    try:
        data = json.loads(content)
        if isinstance(data, list) and len(data) > 0 and "text" in data[0]:
            return parse_gmail_text(data[0]["text"])
        if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
            return data  # Already parsed
    except (json.JSONDecodeError, KeyError):
        pass

    # Fall back to plain text parsing
    return parse_gmail_text(content)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/classify-emails.py <input_file> [--output <output_file>]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    # Load and classify
    emails = load_input(input_file)
    if not emails:
        print("ERROR: No emails found in input file")
        sys.exit(1)

    # Classify each email
    labels = {}  # label_id -> list of message IDs
    label_names = {
        "Label_1": "AI Newsletter",
        "Label_2": "Skool/Revenue",
        "Label_3": "Skool/Message",
        "Label_4": "Skool/Digest",
        "Label_5": "Orders",
        "Label_6": "Promotions",
        "Label_7": "Security",
    }
    label_examples = {k: [] for k in label_names}

    for email in emails:
        from_field = email.get("from", "")
        email_address = extract_email_address(from_field)
        subject = email.get("subject", "")
        email_id = email.get("id", "")

        label = classify_email(email_address, subject, from_field)

        if label not in labels:
            labels[label] = []
        labels[label].append(email_id)

        # Keep first 3 examples per label
        if len(label_examples[label]) < 3:
            label_examples[label].append(subject[:60])

    # Build result
    result = {
        "total": len(emails),
        "labels": {},
        "summary": []
    }

    for label_id in sorted(label_names.keys()):
        ids = labels.get(label_id, [])
        name = label_names[label_id]
        examples = label_examples.get(label_id, [])
        result["labels"][label_id] = ids
        result["summary"].append({
            "label_id": label_id,
            "name": name,
            "count": len(ids),
            "examples": examples,
        })

    # Output
    result_json = json.dumps(result, ensure_ascii=False, indent=2)

    if output_file:
        Path(output_file).write_text(result_json, encoding="utf-8")
        print(f"Classified {len(emails)} emails -> {output_file}")
    else:
        print(result_json)

    # Print summary table to stderr for quick viewing
    print("\n--- Summary ---", file=sys.stderr)
    for s in result["summary"]:
        if s["count"] > 0:
            ex = ", ".join(s["examples"][:2])
            print(f"  {s['name']:15s} {s['count']:4d}  ({ex})", file=sys.stderr)
    print(f"  {'TOTAL':15s} {len(emails):4d}", file=sys.stderr)


if __name__ == "__main__":
    main()
