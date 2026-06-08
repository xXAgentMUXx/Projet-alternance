from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import urllib.parse

def scrape_wtj(keyword="alternance cyber", location="France", job_type=""):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0")
    
    jobs = []
    page = 1
    max_jobs_limit = 100
    
    try:
        driver = webdriver.Chrome(options=options)
        q = urllib.parse.quote_plus(keyword)
        l = urllib.parse.quote_plus(location)
        
        while len(jobs) < max_jobs_limit:
            print(f"WTJ - Scraping page {page}...")
            driver.get(f"https://www.welcometothejungle.com/fr/jobs?query={q}&location={l}&page={page}")
            time.sleep(5)
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.find_all("a", href=True)
            new_jobs = 0
            
            for a_tag in items:
                href = a_tag["href"]
                if "/companies/" in href and "/jobs/" in href:
                    title_elem = a_tag.find(["h3", "h4", "span"])
                    title = title_elem.text.strip() if title_elem else ""
                    if not title or title.lower() == "voir l'offre":
                        continue
                        
                    company = href.split("/companies/")[1].split("/")[0].replace("-", " ").title()
                    full_link = "https://www.welcometothejungle.com" + href if not href.startswith("http") else href
                    
                    if not any(j["link"] == full_link for j in jobs):
                        jobs.append({
                            "title": title,
                            "company": company,
                            "link": full_link,
                            "source": "Welcome to the Jungle",
                            "location": location.capitalize(),
                            "job_type": job_type if job_type else "Non précisé"
                        })
                        new_jobs += 1
            
            if new_jobs == 0:
                print(f"WTJ - Fin des résultats atteinte à la page {page}.")
                break
                
            page += 1
            
        driver.quit()
    except Exception as e:
        print("Erreur WTJ:", e)
        
    print(f"[WTJ] Total final récupéré: {len(jobs)} offres.")
    return jobs
