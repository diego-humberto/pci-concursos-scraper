import hashlib
import re

import scrapy

from pci_scraper.items import ConcursoItem
from config import ESTADOS


class NordesteSpider(scrapy.Spider):
    name = "nordeste"
    start_urls = ["https://www.pciconcursos.com.br/concursos/nordeste/"]

    def parse(self, response):
        current_estado = None

        for element in response.css("div#concursos > div"):
            # State header (div.ua with id = abbreviation)
            if "ua" in (element.attrib.get("class") or ""):
                estado_id = element.attrib.get("id", "")
                if estado_id:
                    current_estado = estado_id
                else:
                    text = element.css("div.uf::text").get("")
                    if "NORDESTE" in text:
                        current_estado = "NORDESTE"
                continue

            # Contest listing (div.na or div.da)
            css_class = element.attrib.get("class") or ""
            if css_class not in ("na", "da"):
                continue

            estado = element.css("div.cc::text").get("").strip()
            if not estado and current_estado:
                estado = current_estado

            if estado not in ESTADOS:
                continue

            url = element.attrib.get("data-url", "")
            titulo = element.css("div.ca a::text").get("").strip()

            cd_parts = element.css("div.cd::text").getall()
            cd_spans = element.css("div.cd span::text").getall()

            vagas_salario = ""
            if cd_parts:
                vagas_salario = cd_parts[0].strip()

            cargos = ""
            escolaridade = ""
            if len(cd_spans) >= 2:
                cargos = cd_spans[0].strip()
                escolaridade = cd_spans[1].strip()
            elif len(cd_spans) == 1:
                escolaridade = cd_spans[0].strip()

            vagas = ""
            salario = ""
            match = re.match(r"(\d+)\s*vagas?\s*até\s*(R\$\s*[\d.,]+)", vagas_salario)
            if match:
                vagas = match.group(1)
                salario = match.group(2)
            else:
                vagas = vagas_salario

            # Collect all text nodes inside div.ce span (including nested)
            prazo_all = element.css("div.ce span ::text").getall()
            prazo = " ".join(p.strip() for p in prazo_all if p.strip())
            prazo = re.sub(r"\s+", " ", prazo).strip()

            item_id = hashlib.md5(f"{titulo}:{estado}:{url}".encode()).hexdigest()

            item = ConcursoItem(
                id=item_id,
                titulo=titulo,
                estado=estado,
                vagas=vagas,
                salario=salario,
                escolaridade=escolaridade,
                cargos=cargos,
                prazo_inscricao=prazo,
                url=url,
                url_edital="",
            )

            if url:
                yield scrapy.Request(
                    url,
                    callback=self.parse_detail,
                    cb_kwargs={"item": item},
                )
            else:
                yield item

    def parse_detail(self, response, item):
        edital_links = response.css("li.pdf a::attr(href)").getall()
        if edital_links:
            item["url_edital"] = edital_links[0]
        yield item
