from playwright.sync_api import sync_playwright
import json

SEARCH = "alternance développeur"
LOCATION = "Montpellier"
MAX_RESULTS = 30


def scrape_meteojob():

    jobs = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=200
        )

        page = browser.new_page()

        print("Ouverture Meteojob...")

        page.goto(
            "https://www.meteojob.com/",
            wait_until="networkidle",
            timeout=60000
        )

        try:
            page.locator(
                "#tarteaucitronPersonalize2"
            ).click(timeout=3000)

            print("Cookies acceptés")

        except:
            print("Pas de popup cookies")

        page.wait_for_timeout(2000)

        print("Recherche...")

        try:

            inputs = page.locator("input")

            inputs.nth(0).fill(SEARCH)
            inputs.nth(1).fill(LOCATION)

            page.keyboard.press("Enter")

        except Exception as e:

            print("Erreur recherche :", e)

            browser.close()
            return

        page.wait_for_load_state("networkidle")

        page.wait_for_timeout(4000)

        links = page.locator("a")

        seen = set()

        for i in range(links.count()):

            try:

                link = links.nth(i)

                title = link.inner_text().strip()

                href = link.get_attribute("href")

                if not href:
                    continue

                if not href.startswith("/jobs/"):
                    continue

                if href in seen:
                    continue

                seen.add(href)

                if href.startswith("/"):
                    href = (
                        "https://www.meteojob.com"
                        + href
                    )

                jobs.append(
                    {
                        "title": title,
                        "location": LOCATION,
                        "url": href,
                        "source": "Meteojob"
                    }
                )

                print(
                    f"{len(jobs)}. {title}"
                )

                if len(jobs) >= MAX_RESULTS:
                    break

            except Exception as e:

                print(
                    "Erreur extraction :",
                    e
                )

        browser.close()

    with open(
        "meteojob_jobs.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            jobs,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"{len(jobs)} offres sauvegardées"
    )


if __name__ == "__main__":
    scrape_meteojob()
