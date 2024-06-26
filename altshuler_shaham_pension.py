import re
import requests
from bs4 import BeautifulSoup
from pension_scraper_interface import PensionScraperInterface
import json
import os
from datetime import datetime, timedelta


class InvestmentRoute:
    def __init__(self, route_name, rate_2024=None, rate_12_month=None, routes_update_date=None):
        self.route_name = route_name
        self.rate_2024 = rate_2024
        self.rate_12_month = rate_12_month
        self.routes_update_date = routes_update_date


def save_links_to_file(links, filename="pension_links.json"):
    data = {
        "links": links,
        "timestamp": datetime.now().isoformat()
    }
    with open(filename, "w") as f:
        json.dump(data, f)


def load_links_from_file(filename="pension_links.json", max_age_days=7):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)

        # Check if the data is not too old
        saved_time = datetime.fromisoformat(data["timestamp"])
        if datetime.now() - saved_time < timedelta(days=max_age_days):
            return data["links"]

    return None


def sites_to_scrape():
    # Try to load links from file
    cached_links = load_links_from_file()
    if cached_links:
        return cached_links

    # If no cached links, scrape the website
    url = "https://www.as-invest.co.il/interstedin/קרנות-פנסיה/קרנות-הפנסיה-שלנו/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    pension_links = []
    responsive_tables = soup.find_all("div", class_="responsiveTable")

    for table in responsive_tables:
        rows = table.find_all("tr")
        for row in rows:
            cell = row.find("td")
            if cell:
                link = cell.find("a", href=True)
                if link:
                    href = link.get("href")
                    title = link.get("title", "")
                    text = link.text.strip()
                    if (("מקיפה" in title or "מקיפה" in text) and
                            "כללית" not in title and "כללית" not in text):
                        full_url = f"https://www.as-invest.co.il{href}"
                        pension_links.append((full_url, title or text))

    # Save the new links to file
    save_links_to_file(pension_links)

    return pension_links

class AltshulerShahamPensionScraper(PensionScraperInterface):
    def scrape(self):
        sites = sites_to_scrape()
        investment_routes = []

        # Extract the update date once
        update_date = None
        if sites:
            response = requests.get(sites[0][0])  # Get the first site
            soup = BeautifulSoup(response.content, "html.parser")
            sub_title = soup.find("div", class_="subTitle")
            if sub_title:
                date_match = re.search(r'\d{2}\.\d{2}\.\d{4}', sub_title.text)
                if date_match:
                    update_date = date_match.group()

        for url, route_name in sites:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            tab_pane = soup.find("li", class_="tab-pane active", id="tabFilter2")
            if tab_pane:
                yield_list = tab_pane.find("ul", class_="yieldList")
                if yield_list:
                    rate_2024 = None
                    rate_12_month = None

                    for li in yield_list.find_all("li"):
                        number = li.find("div", class_="number")
                        text = li.find("p", class_="text")
                        if number and text:
                            number_text = number.text.strip().rstrip('%')
                            text_content = text.text.strip()

                            if "תשואה מצטברת" in text_content:
                                rate_2024 = number_text
                            elif "תשואה ממוצעת שנתית ל-12" in text_content:
                                rate_12_month = number_text

                        if rate_2024 and rate_12_month:
                            break

                    investment_route = InvestmentRoute(
                        route_name=route_name,
                        rate_2024=rate_2024,
                        rate_12_month=rate_12_month,
                        routes_update_date=update_date
                    )
                    investment_routes.append(investment_route)

        best_route = max(investment_routes,
                         key=lambda x: float(x.rate_2024.rstrip('%')) if x.rate_2024 is not None else float('-inf'))

        return best_route
