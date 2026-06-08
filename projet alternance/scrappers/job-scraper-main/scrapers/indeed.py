from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

import urllib.parse

def scrape_indeed(keyword="alternance cyber", location="France", job_type=""):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    jobs = []
    start_param = 0
    max_jobs_limit = 300 # Limite de sécurité pour ne pas tourner pendant 3 heures
    
    try:
        driver = webdriver.Chrome(options=options)
        q = urllib.parse.quote_plus(keyword)
        l = urllib.parse.quote_plus(location)
        
        while len(jobs) < max_jobs_limit:
            print(f"Indeed - Scraping page (start={start_param})...")
            driver.get(f"https://fr.indeed.com/jobs?q={q}&l={l}&start={start_param}")
            time.sleep(4)
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            page_jobs = soup.select("td.resultContent")
            
            if not page_jobs:
                print("Indeed - Plus d'offres trouvées ou sécurité atteinte.")
                break
                
            new_jobs = 0
            for job in page_jobs:
                title_elem = job.select_one("h2.jobTitle span")
                company_elem = job.select_one("span[data-testid='company-name']")
                link_elem = job.select_one("h2.jobTitle a")
                loc_elem = job.select_one("div[data-testid='text-location']")
                
                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    company = company_elem.text.strip() if company_elem else "Entreprise confidentielle"
                    href = link_elem.get("href", "")
                    
                    # Extraction précise de la ville depuis le html sinon fallback
                    actual_location = loc_elem.text.strip() if loc_elem else location.capitalize()
                    
                    if not href.startswith("http"):
                        href = "https://fr.indeed.com" + href
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "link": href,
                        "source": "Indeed",
                        "location": actual_location,
                        "job_type": job_type if job_type else "Non précisé"
                    })
                    new_jobs += 1
            
            if new_jobs == 0:
                print("Indeed - Plus de nouvelles offres extraites.")
                break
            
            # Vérifier s'il y a un bouton page suivante ('aria-label' contenant Suivant ou 'data-testid="pagination-page-next"')
            next_button = soup.select_one("a[data-testid='pagination-page-next']")
            if not next_button:
                print("Indeed - Fin des résultats (pas de bouton suivant).")
                break
                
            start_param += 10 # Indeed passe les pages de 10 en 10
            
        driver.quit()
    except Exception as e:
        print("Erreur Indeed:", e)
    
    print(f"[Indeed] Total final récupéré: {len(jobs)} offres.")
    return jobs