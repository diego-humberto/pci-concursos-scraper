# PCI Concursos Scraper - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Scraper Scrapy que monitora concursos do Nordeste no pciconcursos.com.br e envia notificacoes WhatsApp via CallMeBot, rodando automaticamente no GitHub Actions.

**Architecture:** Spider Scrapy com 2 etapas (listagem + detalhes) -> Pipeline compara com JSON de concursos ja vistos -> Notificador envia mensagem WhatsApp via CallMeBot API. Persistencia via `data/seen.json` commitado automaticamente pelo GitHub Actions.

**Tech Stack:** Python 3.11, Scrapy, requests, GitHub Actions

---

## Estrutura HTML do site (referencia)

### Pagina de listagem (`/concursos/nordeste/`)

- Container principal: `div#concursos`
- Header de estado: `div.ua` com `div.uf` contendo nome do estado, `id` = sigla (ex: `id="AL"`)
- Cada concurso: `div.na` ou `div.da` (primeira entrada do estado)
  - `data-url` = URL da pagina de detalhes
  - `div.ca > a` = titulo/nome do orgao (href = URL detalhes)
  - `div.cc` = sigla do estado (ex: "AL")
  - `div.cd` = vagas, salario, cargos, escolaridade (texto com `<br>` e `<span>`)
  - `div.ce > span` = prazo de inscricao

### Pagina de detalhes (`/noticias/...`)

- Lista de cargos: `<ul><li>` com cargos e vagas
- Link do edital: `li.pdf > a[href]` com URL para PDF em `arq.pciconcursos.com.br`

---

### Task 1: Inicializar projeto Scrapy

**Files:**
- Create: `requirements.txt`
- Create: `pci_scraper/__init__.py`
- Create: `pci_scraper/settings.py`
- Create: `pci_scraper/items.py`
- Create: `pci_scraper/pipelines.py` (vazio por enquanto)
- Create: `pci_scraper/spiders/__init__.py`
- Create: `config.py`
- Create: `.gitignore`

**Step 1: Criar requirements.txt**

```
scrapy>=2.11
requests>=2.31
```

**Step 2: Criar .gitignore**

```
__pycache__/
*.pyc
*.pyo
.env
.scrapy/
*.log
```

**Step 3: Criar config.py**

```python
import os

ESTADOS = ["PE", "PB", "RN", "AL", "BA", "SE"]

ESCOLARIDADES_ACEITAS = ["Médio", "Superior"]

CALLMEBOT_PHONE = os.environ.get("CALLMEBOT_PHONE", "")
CALLMEBOT_APIKEY = os.environ.get("CALLMEBOT_APIKEY", "")

SEEN_FILE = os.path.join(os.path.dirname(__file__), "data", "seen.json")
```

**Step 4: Criar pci_scraper/items.py**

```python
import scrapy


class ConcursoItem(scrapy.Item):
    id = scrapy.Field()
    titulo = scrapy.Field()
    estado = scrapy.Field()
    vagas = scrapy.Field()
    salario = scrapy.Field()
    escolaridade = scrapy.Field()
    cargos = scrapy.Field()
    prazo_inscricao = scrapy.Field()
    url = scrapy.Field()
    url_edital = scrapy.Field()
```

**Step 5: Criar pci_scraper/settings.py**

```python
BOT_NAME = "pci_scraper"

SPIDER_MODULES = ["pci_scraper.spiders"]
NEWSPIDER_MODULE = "pci_scraper.spiders"

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 3

CONCURRENT_REQUESTS = 1

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

ITEM_PIPELINES = {
    "pci_scraper.pipelines.FilterPipeline": 100,
    "pci_scraper.pipelines.DeduplicatePipeline": 200,
    "pci_scraper.pipelines.NotifyPipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

LOG_LEVEL = "INFO"
```

**Step 6: Criar __init__.py vazios**

Criar `pci_scraper/__init__.py` e `pci_scraper/spiders/__init__.py` como arquivos vazios.

**Step 7: Criar pci_scraper/pipelines.py (esqueleto)**

```python
from scrapy.exceptions import DropItem


class FilterPipeline:
    """Filtra concursos por escolaridade."""

    def process_item(self, item, spider):
        raise NotImplementedError


class DeduplicatePipeline:
    """Remove concursos ja notificados."""

    def process_item(self, item, spider):
        raise NotImplementedError


class NotifyPipeline:
    """Envia notificacao via WhatsApp."""

    def process_item(self, item, spider):
        raise NotImplementedError
```

**Step 8: Instalar dependencias e verificar**

Run: `pip install -r requirements.txt`
Expected: Scrapy e requests instalados com sucesso

**Step 9: Commit**

```bash
git init
git add .
git commit -m "feat: initialize scrapy project with config and item model"
```

---

### Task 2: Implementar o Spider principal (nordeste.py)

**Files:**
- Create: `pci_scraper/spiders/nordeste.py`

**Step 1: Criar o spider**

```python
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
            # Header de estado (div.ua com id = sigla)
            if "ua" in (element.attrib.get("class") or ""):
                estado_id = element.attrib.get("id", "")
                if estado_id:
                    current_estado = estado_id
                else:
                    # Header REGIAO NORDESTE sem id, extrair do texto
                    text = element.css("div.uf::text").get("")
                    if "NORDESTE" in text:
                        current_estado = "NORDESTE"
                continue

            # Listing de concurso (div.na ou div.da)
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

            cd_text = element.css("div.cd").get("")
            vagas_salario = ""
            escolaridade = ""
            cargos = ""

            # Parse div.cd content
            cd_parts = element.css("div.cd::text").getall()
            cd_spans = element.css("div.cd span::text").getall()

            # First text node: "X vagas até R$ Y"
            if cd_parts:
                vagas_salario = cd_parts[0].strip()

            # Spans: cargos and escolaridade
            if len(cd_spans) >= 2:
                cargos = cd_spans[0].strip()
                escolaridade = cd_spans[1].strip()
            elif len(cd_spans) == 1:
                escolaridade = cd_spans[0].strip()

            # Parse vagas and salario
            vagas = ""
            salario = ""
            match = re.match(r"(\d+)\s*vagas?\s*até\s*(R\$\s*[\d.,]+)", vagas_salario)
            if match:
                vagas = match.group(1)
                salario = match.group(2)
            else:
                vagas = vagas_salario

            prazo = element.css("div.ce span::text").get("").strip()
            # Handle multiline dates (e.g. "31/03 a\n06/04/2026")
            prazo_parts = element.css("div.ce span *::text").getall()
            if prazo_parts:
                prazo = " ".join(p.strip() for p in [prazo] + prazo_parts if p.strip())
                # Deduplicate
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
        # Extract edital PDF link
        edital_links = response.css("li.pdf a::attr(href)").getall()
        if edital_links:
            item["url_edital"] = edital_links[0]

        yield item
```

**Step 2: Testar o spider em modo dry-run**

Run: `cd C:/Users/Humberto/Downloads/PCI-CONCURSOS && python -m scrapy crawl nordeste -o test_output.json -s LOG_LEVEL=INFO --nolog 2>&1 | head -5`

Ou simplesmente: `python -m scrapy crawl nordeste -o test_output.json`

Expected: Arquivo `test_output.json` com concursos extraidos

**Step 3: Verificar output e limpar**

Run: `python -c "import json; data=json.load(open('test_output.json')); print(f'{len(data)} concursos'); print(json.dumps(data[0], indent=2, ensure_ascii=False))" && rm test_output.json`

Expected: Lista de concursos com campos preenchidos

**Step 4: Commit**

```bash
git add pci_scraper/spiders/nordeste.py
git commit -m "feat: add nordeste spider with listing + detail parsing"
```

---

### Task 3: Implementar o notificador CallMeBot

**Files:**
- Create: `notifier.py`

**Step 1: Criar notifier.py**

```python
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
```

**Step 2: Testar formatacao da mensagem**

Run: `python -c "from notifier import format_message; print(format_message({'estado':'PE','titulo':'Teste','vagas':'10','salario':'R$ 5.000,00','escolaridade':'Superior','cargos':'Analista','prazo_inscricao':'01/03/2026','url':'https://example.com','url_edital':'https://example.com/edital.pdf'}))"`

Expected: Mensagem formatada corretamente

**Step 3: Commit**

```bash
git add notifier.py
git commit -m "feat: add CallMeBot WhatsApp notifier"
```

---

### Task 4: Implementar as Pipelines (filtro, deduplicacao, notificacao)

**Files:**
- Modify: `pci_scraper/pipelines.py`
- Create: `data/seen.json`

**Step 1: Criar data/seen.json inicial**

```json
{}
```

**Step 2: Implementar pipelines.py completo**

```python
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
```

**Step 3: Testar pipeline de filtro com escolaridade invalida**

Run: `python -c "
from pci_scraper.pipelines import FilterPipeline
from scrapy.exceptions import DropItem
p = FilterPipeline()
try:
    p.process_item({'escolaridade': 'Fundamental'}, None)
    print('FAIL: should have dropped')
except DropItem:
    print('OK: dropped Fundamental')
item = p.process_item({'escolaridade': 'Médio / Superior'}, None)
print(f'OK: kept {item[\"escolaridade\"]}')
"`

Expected: `OK: dropped Fundamental` e `OK: kept Médio / Superior`

**Step 4: Commit**

```bash
git add pci_scraper/pipelines.py data/seen.json
git commit -m "feat: add filter, dedup, and notify pipelines"
```

---

### Task 5: Criar main.py (entry point)

**Files:**
- Create: `main.py`

**Step 1: Criar main.py**

```python
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "pci_scraper.settings")

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from pci_scraper.spiders.nordeste import NordesteSpider


def main():
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(NordesteSpider)
    process.start()


if __name__ == "__main__":
    main()
```

**Step 2: Testar execucao local (sem enviar WhatsApp)**

Run: `cd C:/Users/Humberto/Downloads/PCI-CONCURSOS && python main.py`

Expected: Spider roda, filtra concursos, salva em `data/seen.json`. WhatsApp nao envia (sem credenciais).

**Step 3: Verificar seen.json foi populado**

Run: `python -c "import json; data=json.load(open('data/seen.json')); print(f'{len(data)} concursos salvos')"`

Expected: Numero de concursos salvos > 0

**Step 4: Commit**

```bash
git add main.py
git commit -m "feat: add main entry point"
```

---

### Task 6: Criar GitHub Actions workflow

**Files:**
- Create: `.github/workflows/scrape.yml`

**Step 1: Criar o workflow**

```yaml
name: PCI Concursos Scraper

on:
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  scrape:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run scraper
        env:
          CALLMEBOT_PHONE: ${{ secrets.CALLMEBOT_PHONE }}
          CALLMEBOT_APIKEY: ${{ secrets.CALLMEBOT_APIKEY }}
        run: python main.py

      - name: Commit updated seen.json
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/seen.json
          git diff --staged --quiet || git commit -m "chore: update seen concursos [skip ci]"
          git push
```

**Step 2: Validar YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/scrape.yml')); print('YAML valido')" 2>/dev/null || python -c "print('instalar pyyaml para validar ou verificar manualmente')"`

**Step 3: Commit**

```bash
git add .github/workflows/scrape.yml
git commit -m "feat: add GitHub Actions workflow for scheduled scraping"
```

---

### Task 7: Teste de integracao local completo

**Step 1: Limpar seen.json para testar do zero**

Run: `echo '{}' > data/seen.json`

**Step 2: Rodar o spider e verificar que seen.json foi atualizado**

Run: `python main.py`

Expected: Spider roda, concursos sao filtrados e salvos em seen.json

**Step 3: Rodar novamente e verificar que nao ha duplicatas**

Run: `python main.py 2>&1 | grep -i "already seen\|drop"`

Expected: Todos os concursos sao dropados como "already seen"

**Step 4: Commit final**

```bash
git add -A
git commit -m "feat: PCI Concursos scraper ready for deployment"
```

---

### Task 8: Setup do repositorio GitHub e deploy

**Step 1: Criar repositorio no GitHub**

Run: `gh repo create pci-concursos-scraper --public --source=. --push`

**Step 2: Configurar secrets do CallMeBot**

O usuario deve:
1. Registrar no CallMeBot: enviar "I allow callmebot to send me messages" para +34 644 23 71 12 no WhatsApp
2. Anotar a API key recebida
3. Configurar secrets no GitHub:

Run:
```bash
gh secret set CALLMEBOT_PHONE
gh secret set CALLMEBOT_APIKEY
```

**Step 3: Disparar workflow manualmente para testar**

Run: `gh workflow run scrape.yml`

**Step 4: Verificar execucao**

Run: `gh run list --workflow=scrape.yml --limit=1`

Expected: Workflow executado com sucesso
