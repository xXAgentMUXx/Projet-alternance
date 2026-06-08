from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

import urllib.parse

def scrape_hellowork(keyword="alternance cyber", location="France", job_type=""):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    jobs = []
    page = 1
    max_jobs_limit = 300
    
    try:
        driver = webdriver.Chrome(options=options)
        q = urllib.parse.quote_plus(keyword)
        l = urllib.parse.quote_plus(location)
        
        while len(jobs) < max_jobs_limit:
            print(f"HelloWork - Scraping page {page}...")
            # HelloWork utilise p=1, p=2... pour la pagination
            driver.get(f"https://www.hellowork.com/fr-fr/emploi/recherche.html?k={q}&l={l}&p={page}")
            time.sleep(4)
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            items = soup.find_all("h3")
            new_jobs = 0
            
            for item in items:
                a_tag = item.find_parent("a") or item.find("a")
                if a_tag and "href" in a_tag.attrs:
                    title = item.text.strip()
                    href = a_tag["href"]
                    company_elem = item.find_next("span")
                    company = company_elem.text.strip() if company_elem else "HelloWork"
                    
                    loc_elem = item.find_parent("li")
                    if loc_elem:
                        # Try to extract from standard hellowork spans
                        loc_spans = loc_elem.find_all("span", class_="tw-text-sm")
                        actual_location = loc_spans[-1].text.strip() if len(loc_spans) > 1 else location.capitalize()
                    else:
                        actual_location = location.capitalize()
                    
                    if not href.startswith("http"):
                        href = "https://www.hellowork.com" + href
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "link": href,
                        "source": "Hellowork",
                        "location": actual_location,
                        "job_type": job_type if job_type else "Non précisé"
                    })
                    new_jobs += 1
            
            # Si aucun nouveau job n'a été trouvé sur la page, c'est la fin des résultats
            if new_jobs == 0:
                print(f"HelloWork - Fin des résultats atteinte à la page {page}.")
                break
                
            page += 1
            
        driver.quit()
    except Exception as e:
        print("Erreur Hellowork:", e)
    
    print(f"[HelloWork] Total final récupéré: {len(jobs)} offres.")
    return jobs