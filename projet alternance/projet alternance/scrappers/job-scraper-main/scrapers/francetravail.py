from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import urllib.parse

def scrape_francetravail(keyword="alternance cyber", location="France", job_type=""):
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
            print(f"France Travail - Scraping page {page}...")
            # Pôle emploi pagination uses "range" but page works too recursively
            driver.get(f"https://candidat.francetravail.fr/offres/recherche?motsCles={q}&lieux={l}&range={page-1}0-{page}0")
            time.sleep(4)
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.find_all("a", href=True)
            new_jobs = 0
            
            for a_tag in items:
                href = a_tag["href"]
                if "/offres/recherche/detail/" in href:
                    title_elem = a_tag.find("h2")
                    title = title_elem.text.strip() if title_elem else a_tag.text.strip()
                    if len(title) < 5:
                        continue
                        
                    company_elem = a_tag.find_next("p", class_="subtext")
                    company = company_elem.text.strip() if company_elem else "France Travail"
                    full_link = "https://candidat.francetravail.fr" + href if not href.startswith("http") else href
                    
                    if not any(j["link"] == full_link for j in jobs):
                        jobs.append({
                            "title": title,
                            "company": company,
                            "link": full_link,
                            "source": "France Travail",
                            "location": location.capitalize(),
                            "job_type": job_type if job_type else "Non précisé"
                        })
                        new_jobs += 1
            
            if new_jobs == 0:
                print(f"France Travail - Fin des résultats atteinte à la page {page}.")
                break
                
            page += 1
            
        driver.quit()
    except Exception as e:
        print("Erreur France Travail:", e)
        
    print(f"[France Travail] Total final récupéré: {len(jobs)} offres.")
    return jobs
