import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SmartResponder:
    """Generate contextually smart email replies without AI API"""
    
    def __init__(self, company_name: str = "Our Company"):
        self.company_name = company_name
        logger.info("✅ Smart Responder initialized")
    
    def generate_reply(self, 
                      subject: str, 
                      body: str, 
                      intent: str,
                      language: str = "en") -> str:
        """
        Generate smart reply based on intent & content
        
        Detects keywords and responds contextually
        """
        
        body_lower = body.lower()
        subject_lower = subject.lower()
        
        # Extract keywords
        has_order = any(w in body_lower for w in ["order", "bought", "purchase", "product"])
        has_refund = any(w in body_lower for w in ["refund", "return", "money back", "refund"])
        has_urgent = any(w in body_lower for w in ["urgent", "asap", "immediately", "rush"])
        has_thanks = any(w in body_lower for w in ["thank", "thanks", "appreciate"])
        
        # Pick reply based on intent & keywords
        if intent == "refund" or has_refund:
            return self._refund_reply(language)
        
        elif intent == "complaint" or ("complain" in body_lower):
            return self._complaint_reply(language)
        
        elif intent == "customer_support" and has_order:
            return self._order_status_reply(language)
        
        elif intent == "customer_support" and has_urgent:
            return self._urgent_reply(language)
        
        elif has_thanks or intent == "thanks":
            return self._thanks_reply(language)
        
        else:
            return self._general_reply(language)
    
    def _order_status_reply(self, lang: str) -> str:
        if lang == "ro":
            return f"""Salut,

Mulțumesc pentru mesaj! Voi verifica statusul comenzii tale și îți voi răspunde în cel mai scurt timp cu informațiile complete.

Voi reveni în maxim 2 ore cu update-ul.

Cu plăcere,
{self.company_name}"""
        else:
            return f"""Hi,

Thank you for reaching out! I'm checking your order status and will get back to you shortly with complete details.

I'll follow up within 2 hours.

Best regards,
{self.company_name}"""
    
    def _refund_reply(self, lang: str) -> str:
        if lang == "ro":
            return f"""Salut,

Mulțumesc pentru mesajul tău. Cererea de rambursare este importantă pentru noi.

Voi escalada acest lucru către managerul nostru care va lua legătura cu tine în maxim 24 de ore cu o soluție.

Cu plăcere,
{self.company_name}"""
        else:
            return f"""Hi,

Thank you for your message. We take refund requests seriously.

I'm escalating this to our manager who will contact you within 24 hours with a solution.

Best regards,
{self.company_name}"""
    
    def _complaint_reply(self, lang: str) -> str:
        if lang == "ro":
            return f"""Salut,

Regret să aud că ai o problemă. Feedback-ul tău ne ajută să îmbunătățim.

Mă voi ocupa personal de aceasta și voi reveni cu o soluție în maxim 24 de ore.

Cu plăcere,
{self.company_name}"""
        else:
            return f"""Hi,

I'm sorry to hear about your issue. Your feedback helps us improve.

I'm taking this personally and will get back to you with a solution within 24 hours.

Best regards,
{self.company_name}"""
    
    def _urgent_reply(self, lang: str) -> str:
        if lang == "ro":
            return f"""Salut,

Am marcat mesajul tău ca URGENT. Echipa noastră se va ocupa prioritar.

Te voi contacta în maxim 1 oră cu update.

Cu plăcere,
{self.company_name}"""
        else:
            return f"""Hi,

I've marked your message as URGENT. Our team is prioritizing this.

I'll contact you within 1 hour with an update.

Best regards,
{self.company_name}"""
    
    def _thanks_reply(self, lang: str) -> str:
        if lang == "ro":
            return f"""Salut,

Mulțumesc pentru cuvintele tale frumoase! Ne bucură să știm că ești mulțumit.

Suntem mereu aici dacă ai nevoie de ajutor.

Cu plăcere,
{self.company_name}"""
        else:
            return f"""Hi,

Thank you for the kind words! We're happy to hear you're satisfied.

We're always here if you need anything.

Best regards,
{self.company_name}"""
    
    def _general_reply(self, lang: str) -> str:
        if lang == "ro":
            return f"""Salut,

Mulțumesc pentru mesajul tău! L-am primit și voi reveni cu un răspuns complet în maxim 2 ore.

Cu plăcere,
{self.company_name}"""
        else:
            return f"""Hi,

Thank you for reaching out! I've received your message and will get back to you with a full response within 2 hours.

Best regards,
{self.company_name}"""

def create_smart_responder(company_name: str = "Our Company") -> SmartResponder:
    return SmartResponder(company_name)
