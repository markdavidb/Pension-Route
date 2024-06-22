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


def extract_update_date(soup):
    for section in soup.select(".insurence_box_section"):
        for span in section.select("span"):
            if "נכון לתאריך" in span.text:
                return span.get_text(strip=True).replace("(", "").replace(")", "")
    return None


class HarelPensionScraper(PensionScraperInterface):
    def scrape(self):
        url = "https://www.harel-group.co.il/long-term-savings/pension/funds/pension/Pages/investment-routes.aspx"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the update date once
        routes_update_date = extract_update_date(soup)

        route_sections = soup.select(".box.insurence_plan.insurence_panle_section")
        all_routes = []  # List to hold all InvestmentRoute objects

        for section in route_sections:
            route_name = section.select_one("a.standard_link.gaType_click").get("title")
            investment_route = InvestmentRoute(route_name, routes_update_date=routes_update_date)

            for li in section.select("ul li"):
                rate_text = li.select_one("strong").text.strip()
                rate_name_text = li.select_one("span").text.strip()

                # Clean up the rate_name_text
                cleaned_text = re.sub(' +', ' ', rate_name_text.replace('\r\n', ' ').strip())

                if '%' in rate_text:
                    if "תשואה מתחילת שנת " in cleaned_text:
                        investment_route.rate_2024 = rate_text
                    elif "תשואה מצטברת 12 חודשים אחרונים" in cleaned_text:
                        investment_route.rate_12_month = rate_text

                # Check if both rates are found
                if investment_route.rate_2024 is not None and investment_route.rate_12_month is not None:
                    break  # Exit the inner loop if both rates are found

            all_routes.append(investment_route)

        # Find the best route based on rate_2024
        best_route = max(all_routes,
                         key=lambda x: float(x.rate_2024.rstrip('%')) if x.rate_2024 is not None else float('-inf'))

        return best_route
