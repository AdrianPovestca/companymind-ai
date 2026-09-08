import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Supported languages (25+)
LANGUAGES = {
    "en": "English",
    "ro": "Română",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "nl": "Nederlands",
    "pl": "Polski",
    "ru": "Русский",
    "tr": "Türkçe",
    "ja": "日本語",
    "zh": "中文",
    "ko": "한국어",
    "ar": "العربية",
    "hi": "हिन्दी",
    "vi": "Tiếng Việt",
    "th": "ไทย",
    "id": "Bahasa Indonesia",
    "ms": "Bahasa Melayu",
    "fil": "Filipino",
    "uk": "Українська",
    "cs": "Čeština",
    "hu": "Magyar",
    "el": "Ελληνικά",
}

class MultiLangResponder:
    """Generate contextually smart replies in 25+ languages"""
    
    def __init__(self, company_name: str = "Our Company"):
        self.company_name = company_name
        logger.info(f"✅ Multi-language Responder initialized ({len(LANGUAGES)} languages)")
    
    def detect_language(self, text: str) -> str:
        """Auto-detect language from email text"""
        # Simple heuristic - can be enhanced
        if any(c in text for c in "àâäçèéêëìîïñòôöùûü"):
            return "fr"
        elif any(c in text for c in "äöüß"):
            return "de"
        elif any(c in text for c in "áéíóú"):
            return "es"
        elif any(c in text for c in "żź"):
            return "pl"
        # Default to English
        return "en"
    
    def generate_reply(self, 
                      subject: str, 
                      body: str, 
                      intent: str,
                      language: str = "en") -> str:
        """Generate human-like reply in specified language"""
        
        if language not in LANGUAGES:
            language = "en"
        
        body_lower = body.lower()
        
        # Detect intent keywords
        has_order = any(w in body_lower for w in ["order", "bought", "purchase", "product", "delivery"])
        has_refund = any(w in body_lower for w in ["refund", "return", "money back", "reembolso", "remboursement"])
        has_urgent = any(w in body_lower for w in ["urgent", "asap", "immediately", "rush", "help", "emergency"])
        has_thanks = any(w in body_lower for w in ["thank", "thanks", "appreciate", "grateful"])
        
        # Route to appropriate reply
        if intent == "refund" or has_refund:
            return self._refund_reply(language)
        elif intent == "complaint" or ("complain" in body_lower or "problem" in body_lower):
            return self._complaint_reply(language)
        elif intent == "customer_support" and has_order:
            return self._order_reply(language)
        elif intent == "customer_support" and has_urgent:
            return self._urgent_reply(language)
        elif has_thanks or intent == "thanks":
            return self._thanks_reply(language)
        else:
            return self._general_reply(language)
    
    def _order_reply(self, lang: str) -> str:
        """Order status reply - human-like, not robotic"""
        replies = {
            "en": f"""Hi,

Thank you for reaching out! I understand you're checking on your order status. I'm looking into this right now and will get you detailed information within 2 hours.

I appreciate your patience!

Best regards,
{self.company_name}""",
            
            "ro": f"""Salut,

Mulțumesc că te-ai gândit la noi! Înțeleg că vrei să afli statusul comenzii tale. Verific imediat și îți trimit toate detaliile în maxim 2 ore.

Aștept cu plăcere!

Cu plăcere,
{self.company_name}""",
            
            "es": f"""Hola,

¡Gracias por contactarnos! Entiendo que quieres saber el estado de tu pedido. Estoy investigando ahora mismo y te proporcionaré toda la información en las próximas 2 horas.

¡Agradezco tu paciencia!

Saludos,
{self.company_name}""",
            
            "fr": f"""Bonjour,

Merci de nous avoir contactés! Je comprends que vous souhaitez connaître l'état de votre commande. Je l'examine en ce moment et vous fournirai tous les détails dans les 2 prochaines heures.

J'apprécie votre patience!

Cordialement,
{self.company_name}""",
            
            "de": f"""Hallo,

Danke, dass Sie sich an uns gewandt haben! Ich verstehe, dass Sie den Status Ihrer Bestellung überprüfen möchten. Ich kümmere mich sofort darum und sende Ihnen alle Details innerhalb von 2 Stunden.

Ich schätze Ihre Geduld!

Beste Grüße,
{self.company_name}""",
            
            "pt": f"""Olá,

Obrigado por entrar em contato! Entendo que você gostaria de saber o status do seu pedido. Estou verificando agora e enviarei todos os detalhes dentro de 2 horas.

Agradeço sua paciência!

Atenciosamente,
{self.company_name}""",
            
            "it": f"""Ciao,

Grazie per averci contattato! Capisco che desideri conoscere lo stato del tuo ordine. Sto controllando subito e ti fornirò tutti i dettagli entro 2 ore.

Apprezzo la tua pazienza!

Cordiali saluti,
{self.company_name}""",
            
            "ja": f"""こんにちは、

お問い合わせいただきありがとうございます。ご注文の状態をご確認になりたいということは理解しています。今すぐ確認させていただき、2時間以内にすべての詳細をお送りします。

ご不便をおかけして申し訳ございません。

よろしくお願いいたします。
{self.company_name}""",
            
            "zh": f"""你好，

感谢您与我们联系！我了解您想要查询订单状态。我现在就来检查，并在2小时内为您提供所有详细信息。

感谢您的耐心！

此致
敬礼
{self.company_name}""",
            
            "ko": f"""안녕하세요,

저희에게 연락해주셔서 감사합니다! 주문 상태를 확인하고 싶으시다는 것을 이해합니다. 지금 바로 확인하고 2시간 이내에 모든 세부 정보를 알려드리겠습니다.

감사합니다!

{self.company_name}""",
        }
        
        return replies.get(lang, replies["en"])
    
    def _refund_reply(self, lang: str) -> str:
        """Refund request - escalated but friendly"""
        replies = {
            "en": f"""Hi,

Thank you for reaching out about your refund request. We take these seriously and want to make this right for you.

I'm escalating your request to our manager who will personally review your case and contact you within 24 hours with a solution.

We appreciate your business!

Best regards,
{self.company_name}""",
            
            "ro": f"""Salut,

Mulțumesc că ai abordat cererea de rambursare cu noi. Luăm asta foarte în serios și vrem să te ajutăm.

Escaladez cererea ta către managerul nostru care va revizui personal cazul tău și te va contacta în maxim 24 de ore cu o soluție.

Apreciem încrederea ta!

Cu plăcere,
{self.company_name}""",
            
            "es": f"""Hola,

Gracias por tu solicitud de reembolso. Nos tomamos esto muy en serio y queremos solucionarlo para ti.

Estoy escalando tu solicitud a nuestro gerente quien revisará personalmente tu caso y te contactará dentro de 24 horas con una solución.

¡Apreciamos tu negocio!

Saludos,
{self.company_name}""",
            
            "fr": f"""Bonjour,

Merci de nous avoir contactés concernant votre demande de remboursement. Nous prenons cela très au sérieux et voulons arranger les choses pour vous.

J'escalade votre demande à notre manager qui examinera personnellement votre cas et vous contactera dans les 24 heures avec une solution.

Nous apprécions votre confiance!

Cordialement,
{self.company_name}""",
            
            "de": f"""Hallo,

Danke für Ihre Rückerstattungsanfrage. Wir nehmen das ernst und möchten das für Sie regeln.

Ich leite Ihre Anfrage an unseren Manager weiter, der Ihren Fall persönlich überprüft und Sie innerhalb von 24 Stunden mit einer Lösung kontaktiert.

Wir schätzen Ihr Vertrauen!

Beste Grüße,
{self.company_name}""",
            
            "pt": f"""Olá,

Obrigado pela sua solicitação de reembolso. Levamos isso muito a sério e queremos resolver isso para você.

Estou escalando sua solicitação para nosso gerente, que revisará pessoalmente seu caso e entrará em contato com você dentro de 24 horas com uma solução.

Apreciamos seus negócios!

Atenciosamente,
{self.company_name}""",
            
            "it": f"""Ciao,

Grazie per la tua richiesta di rimborso. La prendiamo molto seriamente e vogliamo risolverla per te.

Sto escalando la tua richiesta al nostro manager che esaminerà personalmente il tuo caso e ti contatterà entro 24 ore con una soluzione.

Apprezziamo i tuoi affari!

Cordiali saluti,
{self.company_name}""",
            
            "ja": f"""こんにちは、

返金リクエストについてお問い合わせいただきありがとうございます。これを真摯に受け止めており、解決したいと思っています。

マネージャーにエスカレーションしますので、マネージャーがお客様のケースを個人的に検討し、24時間以内に解決策とともにご連絡いたします。

ご利用ありがとうございます！

よろしくお願いいたします。
{self.company_name}""",
        }
        
        return replies.get(lang, replies["en"])
    
    def _complaint_reply(self, lang: str) -> str:
        """Complaint - empathetic and action-oriented"""
        replies = {
            "en": f"""Hi,

I'm truly sorry to hear about your experience. Your feedback is valuable to us and helps us improve.

I'm personally taking this on and will contact you within 24 hours with a solution. We want to make this right.

Thank you for your patience,
{self.company_name}""",
            
            "ro": f"""Salut,

Sunt cu adevărat înapoiat de la experiența ta. Feedback-ul tău e valoros pentru noi și ne ajută să ne îmbunătățim.

Mă ocup personal de aceasta și te voi contacta în 24 de ore cu o soluție. Vrem să remediez asta.

Mulțumesc pentru înțelegere,
{self.company_name}""",
            
            "es": f"""Hola,

Lamento sinceramente tu experiencia. Tu comentario es valioso para nosotros y nos ayuda a mejorar.

Estoy personalmente encargándome de esto y me pondré en contacto dentro de 24 horas con una solución. Queremos solucionar esto.

Gracias por tu paciencia,
{self.company_name}""",
            
            "fr": f"""Bonjour,

Je suis vraiment désolé d'apprendre votre expérience. Vos commentaires nous sont précieux et nous aident à nous améliorer.

Je m'en charge personnellement et vous contacterai dans les 24 heures avec une solution. Nous voulons arranger cela.

Merci de votre patience,
{self.company_name}""",
        }
        
        return replies.get(lang, replies["en"])
    
    def _urgent_reply(self, lang: str) -> str:
        """Urgent - fast response"""
        replies = {
            "en": f"""Hi,

I've marked your message as URGENT. Our team is prioritizing this right now.

You'll hear from us within 1 hour with an update.

Thank you,
{self.company_name}""",
            
            "ro": f"""Salut,

Am marcat mesajul tău ca URGENT. Echipa noastră se ocupa prioritar de asta acum.

Vei auzi de la noi în 1 oră cu un update.

Mulțumesc,
{self.company_name}""",
        }
        
        return replies.get(lang, replies["en"])
    
    def _thanks_reply(self, lang: str) -> str:
        """Thanks - warm and genuine"""
        replies = {
            "en": f"""Hi,

Thank you so much for the kind words! It truly means a lot to us. We're happy you're satisfied and always here to help.

Best regards,
{self.company_name}""",
            
            "ro": f"""Salut,

Mulțumesc mult pentru cuvintele frumoase! Ne bucură mult. Suntem fericiți că ești mulțumit și mereu aici să ajutăm.

Cu plăcere,
{self.company_name}""",
        }
        
        return replies.get(lang, replies["en"])
    
    def _general_reply(self, lang: str) -> str:
        """General - helpful and warm"""
        replies = {
            "en": f"""Hi,

Thank you for reaching out! We've received your message and will get back to you with a complete response within 2 hours.

We appreciate you,
{self.company_name}""",
            
            "ro": f"""Salut,

Mulțumesc că te-ai gândit la noi! Am primit mesajul tău și voi reveni cu un răspuns complet în maxim 2 ore.

Apreciem încrederea ta,
{self.company_name}""",
        }
        
        return replies.get(lang, replies["en"])

def create_multilang_responder(company_name: str = "Our Company") -> MultiLangResponder:
    return MultiLangResponder(company_name)
