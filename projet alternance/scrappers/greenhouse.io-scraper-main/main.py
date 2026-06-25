#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import time
import re
import json
import sys


# -------------------------
# CHROME
# -------------------------

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)


# -------------------------
# GET JOB LINKS
# -------------------------

def get_openings(job_board):

    driver.get(job_board)

    links = driver.find_elements(By.TAG_NAME, "a")

    found = set()

    for link in links:

        href = link.get_attribute("href")

        if not href:
            continue

        if "/jobs/" in href:
            found.add(href.split("?")[0])

    return list(found)


# -------------------------
# TITLE
# -------------------------

def get_job_title():

    selectors = [
        "h1",
        "[data-testid='job-title']",
        ".job__title",
        ".app-title",
    ]

    for selector in selectors:

        try:

            title = driver.find_element(
                By.CSS_SELECTOR,
                selector
            ).text.strip()

            if title:
                return title

        except:
            pass

    return "Unknown Title"


# -------------------------
# LOCATION
# -------------------------

def get_location():

    selectors = [
        ".location",
        ".job__location",
        "[data-testid='job-location']",
    ]

    for selector in selectors:

        try:

            location = driver.find_element(
                By.CSS_SELECTOR,
                selector
            ).text.strip()

            if location:
                return location

        except:
            pass

    return ""


# -------------------------
# DATE
# -------------------------

def get_date_posted():

    scripts = driver.find_elements(
        By.XPATH,
        "//script[@type='application/ld+json']"
    )

    for script in scripts:

        try:

            data = json.loads(
                script.get_attribute("innerHTML")
            )

            if isinstance(data, dict):

                if "datePosted" in data:
                    return data["datePosted"]

                if "@graph" in data:

                    for item in data["@graph"]:

                        if (
                            isinstance(item, dict)
                            and "datePosted" in item
                        ):
                            return item["datePosted"]

            elif isinstance(data, list):

                for item in data:

                    if (
                        isinstance(item, dict)
                        and "datePosted" in item
                    ):
                        return item["datePosted"]

        except:
            pass

    try:

        meta = driver.find_element(
            By.CSS_SELECTOR,
            "meta[property='article:published_time']"
        )

        return meta.get_attribute("content")

    except:
        pass

    return None


# -------------------------
# COMPANY NAME
# -------------------------

def get_company_name(board_url):

    match = re.search(
        r"boards\.greenhouse\.io/([^/?]+)",
        board_url
    )

    if match:
        return match.group(1)

    return "Unknown Company"


# -------------------------
# SCRAPE
# -------------------------

def scrape_jobs(board_url):

    jobs = []

    company = get_company_name(board_url)

    links = get_openings(board_url)

    for link in links:

        try:

            driver.get(link)

            time.sleep(1)

            title = get_job_title()

            location = get_location()

            date_posted = get_date_posted()

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "url": link,
                "date_posted": date_posted,
                "source": "greenhouse",
                "scraped_at": datetime.now().isoformat()
            })

        except Exception as e:

            print(
                f"Erreur job {link}: {e}",
                file=sys.stderr
            )

    return jobs


# -------------------------
# RUN
# -------------------------

def main():

    try:

        if len(sys.argv) >= 3:

            # FastAPI :
            # py main.py keyword board_url

            board_url = sys.argv[2]

        elif len(sys.argv) == 2:

            board_url = sys.argv[1]

        else:

            print(
                json.dumps({
                    "error": "Missing Greenhouse URL"
                })
            )

            return

        jobs = scrape_jobs(board_url)

        print(
            json.dumps(
                jobs,
                ensure_ascii=False
            )
        )

    except Exception as e:

        print(
            json.dumps({
                "error": str(e)
            })
        )

    finally:

        driver.quit()


if __name__ == "__main__":
    main()