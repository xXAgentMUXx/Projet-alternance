from abc import ABC, abstractmethod


class scraping_jobs(ABC):
    def __init__(self, keyword, contract_type):
        self.s_job = keyword
        self.type_contract = contract_type

    @abstractmethod
    def scrap_job(self):
        raise NotImplementedError