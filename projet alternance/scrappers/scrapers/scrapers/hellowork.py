from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

import os
import re
import sys
import time
import urllib.parse


BASE_URL = "https://www.hellowork.com"
SEARCH_URL = f"{BASE_URL}/fr-fr/emploi/recherche.html"

WAIT_TIME = 4
MAX_RESULTS = 300


def build_driver():

    chrome_options = Options()

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option(
        "excludeSwitches",
        ["enable-logging"]
    )

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver_path = "/usr/bin/chromedriver"
    browser_path = "/usr/bin/chromium"

    silent_log = open(os.devnull, "w")

    if os.path.exists(driver_path):
        chrome_options.binary_location = browser_path
        service = Service(
            executable_path=driver_path,
            log_output=silent_log
        )
    else:
        service = Service(log_output=silent_log)

    return webdriver.Chrome(service=service, options=chrome_options)


def normalize(text):

    if not text:
        return ""

    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def build_search_url(keyword, city, page):
    return (
        f"{SEARCH_URL}"
        f"?k={urllib.parse.quote_plus(keyword)}"
        f"&l={urllib.parse.quote_plus(city)}"
        f"&p={page}"
    )


def extract_location(container, default_city):
    spans = container.find_all("span", class_="tw-text-sm")

    if len(spans) > 1:
        return normalize(spans[-1].text)

    return normalize(default_city.capitalize())


def extract_offer(title_node, city, contract):

    parent_link = title_node.find_parent("a") or title_node.find("a")

    if parent_link is None:
        return None

    if "href" not in parent_link.attrs:
        return None

    url = parent_link["href"]

    if not url.startswith("http"):
        url = BASE_URL + url

    company_node = title_node.find_next("span")

    company = (
        normalize(company_node.text)
        if company_node
        else "HelloWork"
    )

    container = title_node.find_parent("li")

    location = (
        extract_location(container, city)
        if container
        else normalize(city.capitalize())
    )

    return {
        "title": normalize(title_node.text),
        "company": company,
        "link": url,
        "source": "HelloWork",
        "location": location,
        "job_type": contract or "Non précisé",
    }


def scrape_hellowork(
    keyword="alternance cyber",
    location="France",
    job_type=""
):

    results = []
    visited = set()

    browser = None

    try:

        browser = build_driver()

        for current_page in range(1, 100):

            if len(results) >= MAX_RESULTS:
                break

            print(
                f"HelloWork - Scraping page {current_page}...",
                file=sys.stderr
            )

            browser.get(
                build_search_url(
                    keyword,
                    location,
                    current_page
                )
            )

            time.sleep(WAIT_TIME)

            soup = BeautifulSoup(
                browser.page_source,
                "html.parser"
            )

            titles = soup.find_all("h3")

            added = 0

            for title in titles:

                job = extract_offer(
                    title,
                    location,
                    job_type
                )

                if job is None:
                    continue

                if job["link"] in visited:
                    continue

                visited.add(job["link"])
                results.append(job)
                added += 1

            if added == 0:
                print(
                    f"HelloWork - Fin des résultats à la page {current_page}.",
                    file=sys.stderr,
                )
                break

    except Exception as exc:

        print(
            f"Erreur HelloWork : {exc}",
            file=sys.stderr
        )

    finally:

        if browser is not None:
            browser.quit()

    print(
        f"[HelloWork] Total : {len(results)} offres.",
        file=sys.stderr,
    )

    return results