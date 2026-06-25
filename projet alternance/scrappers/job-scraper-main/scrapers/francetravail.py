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
    options.add_argument("--disable-dev-shm-usage")    # REQUIS dans Docker (évite les crashes mémoire)
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # Dans Docker (Debian/Ubuntu), chromium-driver est dans /usr/bin/chromedriver
    # En local (Windows), selenium-manager trouve Chrome automatiquement
    chromedriver_path = "/usr/bin/chromedriver"
    chrome_binary = "/usr/bin/chromium"

    if os.path.exists(chromedriver_path):
        # Mode Docker : utiliser le chromedriver système
        options.binary_location = chrome_binary
        service = Service(executable_path=chromedriver_path)
        return webdriver.Chrome(service=service, options=options)
    else:
        # Mode local : selenium-manager trouve tout seul
        return webdriver.Chrome(options=options)


def scrape_francetravail(keyword="alternance cyber", location="France", job_type=""):
    jobs = []
    page = 1
    max_jobs_limit = 100

    try:
        driver = get_chrome_driver()
        q = urllib.parse.quote_plus(keyword)
        l = urllib.parse.quote_plus(location)

        while len(jobs) < max_jobs_limit:
            print(f"France Travail - Scraping page {page}...")
            driver.get(
                f"https://candidat.francetravail.fr/offres/recherche"
                f"?motsCles={q}&lieux={l}&range={(page-1)*10}-{page*10}"
            )
            time.sleep(4)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.find_all("a", href=True)
            new_jobs = 0

            for a_tag in items:
                href = a_tag["href"]
                if "/offres/recherche/detail/" not in href:
                    continue

                title_elem = a_tag.find("h2")
                title = title_elem.text.strip() if title_elem else a_tag.text.strip()
                if len(title) < 5:
                    continue

                company_elem = a_tag.find_next("p", class_="subtext")
                company = company_elem.text.strip() if company_elem else "France Travail"
                full_link = (
                    "https://candidat.francetravail.fr" + href
                    if not href.startswith("http") else href
                )

                if not any(j["link"] == full_link for j in jobs):
                    jobs.append({
                        "title":    title,
                        "company":  company,
                        "link":     full_link,
                        "source":   "France Travail",
                        "location": location.capitalize(),
                        "job_type": job_type or "Non précisé",
                    })
                    new_jobs += 1

            if new_jobs == 0:
                print(f"France Travail - Fin des résultats à la page {page}.")
                break

            page += 1

        driver.quit()

    except Exception as e:
        print("Erreur France Travail:", e)

    print(f"[France Travail] Total : {len(jobs)} offres.")
    return jobs