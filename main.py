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
