"""Smart email classification and safe auto-reply decisions."""
import re
from src.email_database import get_connection
from src.gmail_email_connector import GmailEmailConnector


class SmartEmailAgent:
    def __init__(self):
        self.gmail = GmailEmailConnector(credentials_path="gmail_oauth_credentials.json")
        self.categories = {
            "sales": ["price", "quote", "offer", "discount", "buy", "purchase"],
            "support": ["help", "issue", "problem", "error", "not working", "broken"],
            "billing": ["invoice", "payment", "refund", "charge", "bill"],
            "inquiry": ["when", "where", "how", "what", "status", "track"],
            "complaint": ["angry", "upset", "unacceptable", "terrible", "worst"],
        }
        self.promotion_markers = ("unsubscribe", "sale", "% off", "promo", "promotion", "newsletter", "marketing", "deal of the day")

    def detect_language(self, text):
        text = text.lower()
        if any(w in text for w in ("sunt", "este", "pentru", "care")): return "ro"
        if any(w in text for w in ("ist", "haben", "können", "bitte")): return "de"
        if any(w in text for w in ("это", "что", "как", "для")): return "ru"
        return "en"

    def categorize_email(self, subject, body):
        text = f"{subject} {body}".lower()
        if any(marker in text for marker in self.promotion_markers):
            return "promotion"
        scores = {name: sum(keyword in text for keyword in words) for name, words in self.categories.items()}
        return max(scores, key=scores.get) if max(scores.values(), default=0) else "general"

    def determine_urgency(self, subject, body, category):
        text = f"{subject} {body}".lower()
        if category == "promotion": return "low"
        markers = ("urgent", "asap", "immediately", "emergency", "!", "broken")
        count = sum(marker in text for marker in markers)
        return "high" if count >= 2 or category in ("complaint", "support") else ("medium" if "important" in text else "low")

    def process_email(self, email):
        category = self.categorize_email(email["subject"], email["body"])
        urgency = self.determine_urgency(email["subject"], email["body"], category)
        # Promotions are ignored: never send an automatic reply.
        should_reply = category != "promotion" and urgency != "high" and category not in ("complaint", "support", "billing")
        return {"category": category, "language": self.detect_language(email["subject"] + " " + email["body"]), "urgency": urgency, "should_auto_reply": should_reply}

    def update_email_db(self, message_id, decision):
        action = "auto_reply" if decision["should_auto_reply"] else ("ignored_promotion" if decision["category"] == "promotion" else "human_review")
        conn = get_connection()
        conn.execute("""UPDATE emails SET status='processed', decision_action=?, decision_reason=?, decision_urgency=?, decision_intent=?, requires_human=? WHERE message_id=?""", (action, f"Category: {decision['category']}", decision["urgency"], decision["category"], int(action == "human_review"), message_id))
        conn.commit(); conn.close()


def main():
    agent = SmartEmailAgent()
    conn = get_connection()
    emails = conn.execute("SELECT message_id, subject, sender, body FROM emails WHERE status NOT IN ('processed','sent') AND message_type='email' LIMIT 25").fetchall()
    conn.close()
    for msg_id, subject, sender, body in emails:
        decision = agent.process_email({"subject": subject, "sender": sender, "body": body})
        agent.update_email_db(msg_id, decision)
        print(f"{subject[:50]} -> {decision['category']} / {decision['urgency']}")


if __name__ == "__main__":
    main()
