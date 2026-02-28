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
