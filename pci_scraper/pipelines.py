from scrapy.exceptions import DropItem


class FilterPipeline:
    def process_item(self, item, spider):
        raise NotImplementedError


class DeduplicatePipeline:
    def process_item(self, item, spider):
        raise NotImplementedError


class NotifyPipeline:
    def process_item(self, item, spider):
        raise NotImplementedError
