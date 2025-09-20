from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
import ask_sdk_core.utils as ask_utils
import requests
import logging
import json
import re
# ─────────────────────────────────────────────────────────────────────────────
# Configuration OpenAI
# ─────────────────────────────────────────────────────────────────────────────
api_key = "sk-xxxxxxxxxxxxxxxx"
model = "gpt-4o-mini"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LaunchRequestHandler(AbstractRequestHandler):
    """Gestionnaire pour le lancement de la Skill."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Mode Chat G.P.T. activé."

        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["chat_history"] = []
        session_attr["last_context"] = None

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Que veux-tu savoir ?")
                .response
        )

class GptQueryIntentHandler(AbstractRequestHandler):
    """Gestionnaire pour l’intention Gpt Query."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GptQueryIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        try:
            query = handler_input.request_envelope.request.intent.slots["query"].value
        except Exception:
            query = None

        session_attr = handler_input.attributes_manager.session_attributes
        if "chat_history" not in session_attr:
            session_attr["chat_history"] = []
        if "last_context" not in session_attr:
            session_attr["last_context"] = None

        # Si pas de question, on reprompt proprement
        if not query or not str(query).strip():
            speak_output = "Je n’ai pas entendu de question. Peux-tu répéter ?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )

        # Détecte une question de suivi
        processed_query, is_followup = process_followup_question(
            query, session_attr.get("last_context")
        )

        # Génère la réponse (avec gestion robuste des erreurs)
        response_text = generate_gpt_response(
            session_attr["chat_history"], processed_query, is_followup
        )

        # Met à jour la session
        session_attr["chat_history"].append((query, response_text))
        session_attr["last_context"] = extract_context(query, response_text)

        # Réponse parlée simple (sans suggestions de suivi)
        reprompt_text = "Tu peux me poser une autre question ou dire stop pour terminer."

        return (
            handler_input.response_builder
                .speak(response_text)
                .ask(reprompt_text)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Gestionnaire générique des erreurs (syntaxe, routage, etc.)."""
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        speak_output = "Désolé, j’ai eu un problème pour exécuter ta demande. Essaie encore."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Que veux-tu savoir ?")
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Gestionnaire pour les intentions Annuler et Stop."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (
            ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input)
            or ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input)
        )

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Fermeture du mode Chat G.P.T."
        return handler_input.response_builder.speak(speak_output).response

def process_followup_question(question, last_context):
    """Détecte si une question est un suivi et retourne (question, est_suivi)."""
    # Indicateurs fréquents de question de suivi en français
    followup_patterns = [
        r'^(quoi|comment|pourquoi|quand|où|qui|lequel|laquelle|lesquels|lesquelles)\s+(est|sont|étais|étaient|fait|font|faut|peut|pourrait|devrait|va)\s',
        r'^(et|mais|donc|alors|aussi)\s',
        r'^(peux|peut|pourrait|pourrais|voudrais|devrais|vas)\s+(tu|vous|il|elle|ils|elles|on|nous)\s',
        r'^(est|sont|étais|étaient|fais|fait|font)\s+(ce|ça|cela|cette|ces|ils|elles)\s',
        r'^(dis[- ]?moi en plus|explique[- ]?moi|détaille[- ]?moi|peux[- ]?tu expliquer)\s*',
        r'^(pourquoi|comment)\s*\?*$'
    ]

    is_followup = False
    q_lower = (question or "").strip().lower()
    for pattern in followup_patterns:
        if re.search(pattern, q_lower):
            is_followup = True
            break

    return question, is_followup

def extract_context(question, response):
    """Extrait un contexte simple pour la suite de la conversation."""
    return {"question": question, "response": response}

def generate_gpt_response(chat_history, new_question, is_followup=False):
    """Génère une réponse GPT en français avec gestion de contexte et d’erreurs.
       NOTE: Cette version ne propose pas de questions de suivi."""
    # Si pas de clé, on renvoie une erreur gentille côté voix
    if not api_key:
        return ("Je ne peux pas répondre pour l’instant car la clé API n’est pas configurée. "
                "Ajoute la variable OPENAI_API_KEY à l’environnement.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    url = "https://api.openai.com/v1/chat/completions"

    # Consigne ferme: rester en FR + utiliser le contexte précédent même si la question est elliptique
    system_message = (
        "Tu es un assistant utile. Réponds toujours en français, en 60 mots ou moins. "
        "Utilise le contexte des échanges précédents pour comprendre les références implicites. "
        "Si c’est ambigu, demande une courte clarification."
    )
    if is_followup:
        system_message += (
            " Ceci est une question de suivi : privilégie la continuité et évite de répéter les détails déjà donnés."
        )

    messages = [{"role": "system", "content": system_message}]

    # Plus d'historique quand c'est une question de suivi
    history_limit = 6
    if is_followup:
        history_limit = 12  # on envoie plus de contexte pour les suivis

    # Injecte les paires Q/R du passé (du plus ancien au plus récent conservé)
    for question, answer in chat_history[-history_limit:]:
        if question:
            messages.append({"role": "user", "content": str(question)})
        if answer:
            messages.append({"role": "assistant", "content": str(answer)})

    # Question courante
    messages.append({"role": "user", "content": str(new_question)})

    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.5  # un peu plus bas pour des réponses stables/consistantes
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=12)
        payload = {}
        try:
            payload = resp.json()
        except Exception:
            logger.error("Réponse non-JSON de l’API OpenAI.")

        if resp.ok and "choices" in payload and payload["choices"]:
            response_text = (
                payload["choices"][0]
                .get("message", {})
                .get("content", "")
            )
            if not response_text:
                response_text = "Désolé, je n’ai pas de réponse pour le moment."
        else:
            # Détail d’erreur si dispo
            err_msg = payload.get("error", {}).get("message", "Erreur inconnue.")
            logger.error(f"API error: {resp.status_code} - {err_msg}")
            response_text = "Désolé, j’ai rencontré un problème pour générer la réponse."

        return response_text.strip()

    except requests.Timeout:
        logger.error("Timeout lors de l’appel à l’API OpenAI.")
        return "Désolé, le service a mis trop de temps à répondre. Réessaie dans un instant."
    except Exception as e:
        logger.error(f"Exception lors de l’appel à l’API OpenAI: {e}")
        return "Désolé, une erreur est survenue pendant le traitement de ta demande."

class ClearContextIntentHandler(AbstractRequestHandler):
    """Gestionnaire pour vider l’historique de conversation."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ClearContextIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["chat_history"] = []
        session_attr["last_context"] = None

        speak_output = "J’ai effacé notre historique de conversation. De quoi veux-tu parler maintenant ?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Je t’écoute.")
                .response
        )

# ─────────────────────────────────────────────────────────────────────────────
# Construction de la Skill
# ─────────────────────────────────────────────────────────────────────────────
sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GptQueryIntentHandler())
sb.add_request_handler(ClearContextIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
