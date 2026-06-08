import json
import re
from urllib.parse import urlencode
from scrapfly import ScrapflyClient, ScrapeConfig

API_KEY = "scp-live-49128b0d33b94a7587e48121c2213f36"

SEARCH_KEYWORD = input("Mot-clé : ")
LOCATION = input("Ville : ")

client = ScrapflyClient(key=API_KEY)


def make_search_url():
    params = {
        "q": SEARCH_KEYWORD.strip(),   
        "l": LOCATION.strip(),
        "from": "searchOnDesktopSerp"
    }
    return "https://fr.indeed.com/jobs?" + urlencode(params)


def parse_search_page(html):

    job_keys = re.findall(r"jk=([a-zA-Z0-9]+)", html)

    job_keys = list(set(job_keys))

    return [{"jobKey": jk} for jk in job_keys]


def parse_job_page(html):
    match = re.findall(r"_initialData=(\{.+?\});", html)

    if not match:
        return None

    data = json.loads(match[0])
    job = data["jobInfoWrapperModel"]["jobInfoModel"]

    return {
        "title": job.get("title"),
        "company": job.get("companyName"),
        "location": job.get("formattedLocation"),
        "description": job.get("jobDescription"),
        "url": job.get("jobUrl")
    }


def scrape_search():
    url = make_search_url()

    print(url)

    result = client.scrape(
        ScrapeConfig(
            url=url,
            asp=True,
            country="fr",
            render_js=True,
            headers={
                "Accept-Language": "fr-FR,fr;q=0.9",
                "User-Agent": "Mozilla/5.0"
            }
        )
    )

    with open("debug_indeed.html", "w", encoding="utf8") as f:
        f.write(result.content)

    return parse_search_page(result.content)


def scrape_details(job_keys):
    jobs = []

    for jk in job_keys:
        print("detail:", jk)

        url = f"https://fr.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={jk}"

        result = client.scrape(
            ScrapeConfig(
                url=url,
                asp=True,
                country="fr",
                render_js=True
            )
        )

        job = parse_job_page(result.content)

        if job:
            jobs.append(job)

    return jobs


def run():
    results = scrape_search()

    keys = [r["jobKey"] for r in results if "jobKey" in r]

    print("offres trouvées :", len(keys))

    jobs = scrape_details(keys)

    with open("indeed_jobs.json", "w", encoding="utf8") as f:
        json.dump(jobs, f, indent=4, ensure_ascii=False)

    print("Terminé :", len(jobs))


if __name__ == "__main__":
    run()