# PCI Concursos Scraper - Design

## Objetivo

Monitorar concursos publicos do Nordeste no site pciconcursos.com.br e enviar notificacoes via WhatsApp (CallMeBot) quando novos concursos forem detectados, rodando automaticamente no GitHub Actions sem precisar manter o computador ligado.

## Requisitos

- **Estados:** PE, PB, RN, AL, BA, SE
- **Escolaridade:** Medio e Superior
- **Frequencia:** A cada 30 minutos via GitHub Actions
- **Notificacao:** WhatsApp via CallMeBot (gratuito)
- **Dados:** Informacoes completas + link do edital (PDF)

## Arquitetura

```
GitHub Actions (cron cada 30 min)
  |
  v
Scrapy Spider --> Compara com seen.json --> CallMeBot WhatsApp
  |                       |
  v                       v
pciconcursos.com.br    data/seen.json (commit automatico)
```

### Fluxo

1. GitHub Actions aciona `main.py` a cada 30 min
2. Spider Scrapy faz scraping da pagina de listagem dos 6 estados
3. Filtra por escolaridade Medio e Superior
4. Para cada concurso novo, entra na pagina de detalhes para pegar link do edital
5. Compara com `data/seen.json` para identificar novos
6. Novos concursos -> envia WhatsApp via CallMeBot
7. Atualiza `data/seen.json` e faz commit automatico

## Estrutura do Projeto

```
PCI-CONCURSOS/
├── pci_scraper/
│   ├── __init__.py
│   ├── settings.py          # Config do Scrapy
│   ├── items.py             # Modelo de dados do concurso
│   ├── pipelines.py         # Pipeline: comparar + notificar
│   └── spiders/
│       └── nordeste.py      # Spider principal (listagem + detalhes)
├── data/
│   └── seen.json            # Concursos ja notificados
├── config.py                # Estados, escolaridade, CallMeBot config
├── notifier.py              # Integracao com CallMeBot API
├── main.py                  # Entry point
├── requirements.txt
├── .github/
│   └── workflows/
│       └── scrape.yml       # GitHub Actions workflow
└── .gitignore
```

## Modelo de Dados (Item)

| Campo             | Tipo   | Descricao                        |
|-------------------|--------|----------------------------------|
| id                | str    | Hash de titulo + estado          |
| titulo            | str    | Nome do orgao/concurso           |
| estado            | str    | UF (PE, PB, RN, AL, BA, SE)     |
| vagas             | str    | Quantidade de vagas              |
| salario           | str    | Salario maximo                   |
| escolaridade      | str    | Nivel exigido                    |
| prazo_inscricao   | str    | Data limite de inscricao         |
| url               | str    | Link para pagina de detalhes     |
| url_edital        | str    | Link para PDF do edital          |
| cargos            | str    | Lista de cargos disponiveis      |

## Formato da Mensagem WhatsApp

```
NOVO CONCURSO - PE

MPAL - Ministerio Publico de Alagoas
27 vagas | Ate R$ 6.243,37
Nivel: Superior
Inscricoes: 01/03 a 15/03/2026
Edital: https://...link-do-pdf...
Detalhes: https://pciconcursos.com.br/...
```

## Spider (2 etapas)

1. **Pagina de listagem** (`/concursos/nordeste/`): extrai dados basicos de cada concurso + URL de detalhes
2. **Pagina de detalhes**: extrai link do edital (PDF) e cargos especificos

## GitHub Actions

- **Cron:** `*/30 * * * *`
- **Passos:** checkout -> setup Python 3.11 -> pip install -> rodar spider -> commit seen.json
- **Secrets:** `CALLMEBOT_PHONE`, `CALLMEBOT_APIKEY`

## Seguranca e Boas Praticas

- `DOWNLOAD_DELAY = 3` (respeitar o site)
- Respeita `robots.txt`
- Credenciais via GitHub Secrets (nunca no codigo)
- Retry automatico do Scrapy em caso de falha
- `seen.json` commitado para persistencia entre execucoes

## Dependencias

- scrapy
- requests (para CallMeBot API)
