from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import sys
import json
import time
import re
import os


def load_prefs() -> dict:
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "auto_search_config.json"
    )
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def title_matches(title: str, keyword: str) -> bool:
    if not keyword:
        return True
    tokens = [t.lower().strip() for t in re.split(r"[\s,/]+", keyword) if len(t.strip()) >= 3]
    if not tokens:
        return True
    return any(t in title.lower() for t in tokens)


options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)


def get_openings(job_board):
    print(f"[DEBUG] Ouverture : {job_board}", file=sys.stderr)
    driver.get(job_board)
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)
    links = driver.find_elements(By.CSS_SELECTOR, "a.posting-title")
    print(f"[DEBUG] {len(links)} offres trouvées", file=sys.stderr)
    found = []
    for link in links:
        href = link.get_attribute("href")
        if href:
            found.append(href)
    return found


def get_job_title():
    selectors = ["div.posting-headline h2", "h2", "h1"]
    for selector in selectors:
        try:
            text = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            if text:
                return text
        except:
            pass
    return "Titre inconnu"


def get_location():
    selectors = ["div.location", ".posting-categories .location"]
    for selector in selectors:
        try:
            text = driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            if text:
                return text
        except:
            pass
    return "Non précisé"


def get_date_posted():
    try:
        scripts = driver.find_elements(
            By.XPATH, "//script[@type='application/ld+json']"
        )
        for script in scripts:
            try:
                data = json.loads(script.get_attribute("innerHTML"))
                if isinstance(data, dict) and "datePosted" in data:
                    return data["datePosted"]
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "datePosted" in item:
                            return item["datePosted"]
            except:
                continue
    except:
        pass
    return None


def get_company_name(board_url):
    match = re.search(r"jobs\.lever\.co/([^/?]+)", board_url)
    if match:
        return match.group(1)
    return ""


def scrape_jobs(url_list, company, keyword=""):
    results = []
    print(f"[Lever] {company} — {len(url_list)} offres brutes | keyword='{keyword}'", file=sys.stderr)

    for job_link in url_list:
        try:
            print(f"[DEBUG] Scraping {job_link}", file=sys.stderr)
            driver.get(job_link)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            title       = get_job_title()
            location    = get_location()
            date_posted = get_date_posted()

            if not title_matches(title, keyword):
                continue

            days_old = None
            if date_posted:
                try:
                    posted   = datetime.strptime(date_posted[:10], "%Y-%m-%d")
                    days_old = (datetime.now() - posted).days
                except:
                    pass

            results.append({
                "title":       title,
                "company":     company,
                "location":    location,
                "date_posted": date_posted,
                "days_old":    days_old,
                "url":         job_link,
                "source":      "Lever",
                "type":        "offre",
                "contract":    [],
                "remote":      "",
                "created_at":  date_posted or "",
                "description": "",
            })

        except Exception as e:
            print(f"[ERROR] {job_link} : {e}", file=sys.stderr)

    print(f"[Lever] {len(results)} offres après filtrage", file=sys.stderr)
    return results

try:
    prefs = load_prefs()

    if len(sys.argv) >= 3:
        keyword     = sys.argv[1] or prefs.get("keyword") or ""
        career_page = sys.argv[2]
    elif len(sys.argv) == 2:
        career_page = sys.argv[1]
        keyword     = prefs.get("keyword") or ""
    else:
        print(json.dumps({"error": "missing lever url"}))
        sys.exit(1)

    if not career_page.startswith("https://jobs.lever.co/"):
        print(json.dumps({"error": f"URL invalide : {career_page}"}))
        sys.exit(1)

    company = get_company_name(career_page)
    start   = time.time()
    links   = get_openings(career_page)
    jobs    = scrape_jobs(links, company, keyword)

    print(json.dumps(jobs, ensure_ascii=False))
    print(f"[DEBUG] terminé en {time.time()-start:.2f}s", file=sys.stderr)

except Exception as e:
    print(json.dumps({"error": str(e)}))

finally:
    driver.quit()