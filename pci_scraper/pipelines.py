import json
import logging
import os

from scrapy.exceptions import DropItem

from config import ESCOLARIDADES_ACEITAS, SEEN_FILE
from notifier import send_whatsapp

logger = logging.getLogger(__name__)


class FilterPipeline:
    """Filtra concursos por escolaridade aceita (Medio ou Superior)."""

    def process_item(self, item, spider):
        escolaridade = item.get("escolaridade", "")
        if any(nivel in escolaridade for nivel in ESCOLARIDADES_ACEITAS):
            return item
        raise DropItem(f"Escolaridade nao aceita: {escolaridade}")


class DeduplicatePipeline:
    """Remove concursos ja notificados, usando data/seen.json."""

    def __init__(self):
        self.seen = {}
        self.seen_file = SEEN_FILE

    def open_spider(self, spider):
        os.makedirs(os.path.dirname(self.seen_file), exist_ok=True)
        if os.path.exists(self.seen_file):
            with open(self.seen_file, "r", encoding="utf-8") as f:
                try:
                    self.seen = json.load(f)
                except json.JSONDecodeError:
                    self.seen = {}
        logger.info(f"Loaded {len(self.seen)} seen concursos")

    def close_spider(self, spider):
        with open(self.seen_file, "w", encoding="utf-8") as f:
            json.dump(self.seen, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(self.seen)} seen concursos")

    def process_item(self, item, spider):
        item_id = item.get("id", "")
        if item_id in self.seen:
            raise DropItem(f"Already seen: {item.get('titulo', '?')}")
        self.seen[item_id] = {
            "titulo": item.get("titulo", ""),
            "estado": item.get("estado", ""),
        }
        return item


class NotifyPipeline:
    """Envia notificacao via WhatsApp para concursos novos."""

    def process_item(self, item, spider):
        send_whatsapp(item)
        return item
