from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

import os
import re
import sys
import time
import urllib.parse


BASE_URL = "https://candidat.francetravail.fr"
SEARCH_URL = f"{BASE_URL}/offres/recherche"

WAIT_TIME = 4
MAX_RESULTS = 100
MAX_PAGES = 30


def build_driver():

    chrome_options = Options()

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver_path = "/usr/bin/chromedriver"
    browser_path = "/usr/bin/chromium"

    if os.path.exists(driver_path):
        chrome_options.binary_location = browser_path

        service = Service(executable_path=driver_path)
        return webdriver.Chrome(service=service, options=chrome_options)

    return webdriver.Chrome(options=chrome_options)


def normalize(value):
    if not value:
        return ""

    value = re.sub(r"[\r\n\t]+", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def make_search_url(keyword, city, page):

    params = (
        f"?motsCles={urllib.parse.quote_plus(keyword)}"
        f"&lieux={urllib.parse.quote_plus(city)}"
        f"&range={(page-1)*10}-{page*10}"
    )

    return SEARCH_URL + params


def extract_offer(node, default_city, contract):

    href = node.get("href", "")

    if "/offres/recherche/detail/" not in href:
        return None

    title_node = node.find("h2")

    title = normalize(
        title_node.text if title_node else node.text
    )

    if len(title) < 5:
        return None

    company_node = node.find_next("p", class_="subtext")

    company = (
        normalize(company_node.text)
        if company_node
        else "France Travail"
    )

    if href.startswith("http"):
        url = href
    else:
        url = BASE_URL + href

    return {
        "title": title,
        "company": company,
        "link": url,
        "source": "France Travail",
        "location": normalize(default_city.capitalize()),
        "job_type": contract or "Non précisé",
    }


def scrape_francetravail(
    keyword="alternance cyber",
    location="France",
    job_type=""
):

    browser = None

    offers = []
    visited = set()

    try:

        browser = build_driver()

        for current_page in range(1, MAX_PAGES + 1):

            if len(offers) >= MAX_RESULTS:
                break

            print(
                f"France Travail - Scraping page {current_page}...",
                file=sys.stderr,
            )

            browser.get(
                make_search_url(
                    keyword,
                    location,
                    current_page,
                )
            )

            time.sleep(WAIT_TIME)

            html = browser.page_source

            soup = BeautifulSoup(
                html,
                "html.parser"
            )

            links = soup.find_all("a", href=True)

            inserted = 0

            for element in links:

                job = extract_offer(
                    element,
                    location,
                    job_type,
                )

                if job is None:
                    continue

                if job["link"] in visited:
                    continue

                visited.add(job["link"])
                offers.append(job)

                inserted += 1

            if inserted == 0:

                print(
                    f"France Travail - Fin des résultats à la page {current_page}.",
                    file=sys.stderr,
                )

                break

    except Exception as exc:

        print(
            f"Erreur France Travail : {exc}",
            file=sys.stderr,
        )

    finally:

        if browser is not None:
            browser.quit()

    print(
        f"[France Travail] Total : {len(offers)} offres.",
        file=sys.stderr,
    )

    return offers