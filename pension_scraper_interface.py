from abc import ABC, abstractmethod


class PensionScraperInterface(ABC):
    @abstractmethod
    def scrape(self):
        pass
