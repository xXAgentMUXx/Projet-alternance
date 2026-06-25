from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import urllib.parse
import os


def get_chrome_driver():
    """Crée un driver Chrome compatible Docker et local."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")               # REQUIS dans Docker
    options.add_argument("--disable-dev-shm-usage")    # REQUIS dans Docker
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    chromedriver_path = "/usr/bin/chromedriver"
    chrome_binary = "/usr/bin/chromium"

    if os.path.exists(chromedriver_path):
        options.binary_location = chrome_binary
        service = Service(executable_path=chromedriver_path)
        return webdriver.Chrome(service=service, options=options)
    else:
        return webdriver.Chrome(options=options)


def scrape_hellowork(keyword="alternance cyber", location="France", job_type=""):
    jobs = []
    page = 1
    max_jobs_limit = 300

    try:
        driver = get_chrome_driver()
        q = urllib.parse.quote_plus(keyword)
        l = urllib.parse.quote_plus(location)

        while len(jobs) < max_jobs_limit:
            print(f"HelloWork - Scraping page {page}...")
            driver.get(
                f"https://www.hellowork.com/fr-fr/emploi/recherche.html"
                f"?k={q}&l={l}&p={page}"
            )
            time.sleep(4)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.find_all("h3")
            new_jobs = 0

            for item in items:
                a_tag = item.find_parent("a") or item.find("a")
                if not a_tag or "href" not in a_tag.attrs:
                    continue

                title = item.text.strip()
                href  = a_tag["href"]

                company_elem = item.find_next("span")
                company = company_elem.text.strip() if company_elem else "HelloWork"

                loc_elem = item.find_parent("li")
                if loc_elem:
                    loc_spans = loc_elem.find_all("span", class_="tw-text-sm")
                    actual_location = (
                        loc_spans[-1].text.strip()
                        if len(loc_spans) > 1
                        else location.capitalize()
                    )
                else:
                    actual_location = location.capitalize()

                if not href.startswith("http"):
                    href = "https://www.hellowork.com" + href

                jobs.append({
                    "title":    title,
                    "company":  company,
                    "link":     href,
                    "source":   "Hellowork",
                    "location": actual_location,
                    "job_type": job_type or "Non précisé",
                })
                new_jobs += 1

            if new_jobs == 0:
                print(f"HelloWork - Fin des résultats à la page {page}.")
                break

            page += 1

        driver.quit()

    except Exception as e:
        print("Erreur Hellowork:", e)

    print(f"[HelloWork] Total : {len(jobs)} offres.")
    return jobs