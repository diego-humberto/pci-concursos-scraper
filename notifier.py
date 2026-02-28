import logging
import urllib.parse

import requests

from config import CALLMEBOT_PHONE, CALLMEBOT_APIKEY

logger = logging.getLogger(__name__)


def format_message(item):
    parts = [
        f"NOVO CONCURSO - {item.get('estado', '?')}",
        "",
        item.get("titulo", "Sem titulo"),
        f"{item.get('vagas', '?')} vagas | Ate {item.get('salario', '?')}"
        if item.get("salario")
        else f"{item.get('vagas', '?')} vagas",
        f"Nivel: {item.get('escolaridade', '?')}",
    ]

    if item.get("cargos"):
        parts.append(f"Cargos: {item['cargos']}")

    if item.get("prazo_inscricao"):
        parts.append(f"Inscricoes: {item['prazo_inscricao']}")

    if item.get("url_edital"):
        parts.append(f"Edital: {item['url_edital']}")

    if item.get("url"):
        parts.append(f"Detalhes: {item['url']}")

    return "\n".join(parts)


def send_whatsapp(item):
    if not CALLMEBOT_PHONE or not CALLMEBOT_APIKEY:
        logger.warning("CallMeBot credentials not configured, skipping notification")
        return False

    message = format_message(item)
    encoded = urllib.parse.quote_plus(message)

    url = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={CALLMEBOT_PHONE}"
        f"&text={encoded}"
        f"&apikey={CALLMEBOT_APIKEY}"
    )

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            logger.info(f"WhatsApp sent: {item.get('titulo', '?')}")
            return True
        else:
            logger.error(f"CallMeBot error {resp.status_code}: {resp.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"CallMeBot request failed: {e}")
        return False
