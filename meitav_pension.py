import re
import requests
from bs4 import BeautifulSoup
from pension_scraper_interface import PensionScraperInterface


class InvestmentRoute:
    def __init__(self, route_name, rate_2024=None, rate_12_month=None, routes_update_date=None):
        self.route_name = route_name
        self.rate_2024 = rate_2024
        self.rate_12_month = rate_12_month
        self.routes_update_date = routes_update_date


def extract_rate(box, label_text):
    for line in box.select("div.Line-Uikit.between"):
        labels = line.select("label.Label-Uikit")
        if len(labels) == 2 and labels[0].text.strip() == label_text:
            return labels[1].text.strip()
    return "N/A"


def extract_update_date(soup):
    for p in soup.select("p"):
        if "התפלגות הנכסים וסך הנכסים נכון לתאריך" in p.text:
            date_match = re.search(r'\d{2}/\d{2}/\d{4}', p.text)
            if date_match:
                return date_match.group()
    return "N/A"


class MeitavPensionScraper(PensionScraperInterface):
    def scrape(self):
        url = "https://www.meitav.co.il/provident_pension/pension_reports/"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the update date once
        routes_update_date = extract_update_date(soup)

        accordion = soup.select(".accordion")
        all_routes = []

        for accordion_item in accordion:
            for item in accordion_item.select(".accordion-item"):
                route_name = item.select_one("h2 a").text.strip() if item.select_one("h2 a") else "N/A"

                w_40_div = item.select_one("div.Rows-Uikit.w-40")
                if w_40_div:
                    box = w_40_div.select_one("div.Rows-Uikit.box")
                    if box and box.select_one("label.Label-Uikit.big").text.strip() == "תשואה נומינלית ברוטו ב-%":
                        rate_2024 = extract_rate(box, "תשואה מתחילת השנה *")
                        rate_12_month = extract_rate(box, "תשואה 12 חודשים**")

                        route = InvestmentRoute(route_name, rate_2024, rate_12_month, routes_update_date)
                        all_routes.append(route)

        # Find the best route based on rate_2024
        best_route = max(all_routes, key=lambda x: x.rate_2024 if x.rate_2024 is not None else float('-inf'))

        return best_route
