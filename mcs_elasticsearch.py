from elasticsearch import Elasticsearch
from typing import Dict

class MCSElasticSearch(object):
    elastic_host = 'localhost'
    elastic_port = 9200
    index_name = ''

    def __init__(self, index_name: str, index_type: str, delete_index: bool, settings: dict):
        MCSElasticSearch.index_name = index_name

        # connect to es
        self.es = Elasticsearch([{'host': MCSElasticSearch.elastic_host, 'port': MCSElasticSearch.elastic_port}])

        # delete index if exists
        if delete_index:
            if self.es.indices.exists(index_name):
                print("Removing existing index " + index_name)
                self.es.indices.delete(index = index_name)

        # create index
        self.es.indices.create(index = index_name, ignore=400, body=settings)

    def bulk_upload(self, bulk_data: dict):
        res = self.es.bulk(index=MCSElasticSearch.index_name , body=bulk_data, refresh=True, request_timeout=30)

        if res['errors']: 
            print("Errors: {}".format(res['errors']))
