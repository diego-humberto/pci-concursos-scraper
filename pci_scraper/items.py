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
