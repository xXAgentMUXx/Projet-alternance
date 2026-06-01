from playwright.sync_api import sync_playwright
import json

SEARCH = "alternance développeur"
LOCATION = "Montpellier"
MAX_RESULTS = 30


def scrape_meteojob():
    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,   # mettre True plus tard
            slow_mo=200
        )

        page = browser.new_page()

        print("Ouverture Meteojob...")
        page.goto("https://www.meteojob.com/", timeout=60000)

        # ----- Gestion cookies -----
        try:
            page.locator("#tarteaucitronPersonalize2").click(timeout=3000)
            print("Cookies acceptés")
        except:
            print("Pas de popup cookies")

        # suppression forcée de la bannière si elle reste
        page.evaluate("""
        const el = document.getElementById('tarteaucitronRoot');
        if (el) el.remove();
        """)

        page.wait_for_timeout(1500)

        # ----- Recherche -----
        print("Recherche...")

        try:
            # champ métier visible
            job_input = page.locator("input[name='what']:visible").first
            job_input.fill(SEARCH)

            # champ localisation visible
            location_input = page.locator("input[name='where']:visible").first
            location_input.fill(LOCATION)

            page.keyboard.press("Enter")

        except Exception as e:
            print("Erreur champs recherche :", e)
            browser.close()
            return

        # attendre résultats
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # ----- Scraping résultats -----
        cards = page.locator("article")
        count = min(cards.count(), MAX_RESULTS)

        print(f"{count} offres trouvées")

        for i in range(count):
            try:
                card = cards.nth(i)

                title = card.locator("h2").inner_text()

                link = card.locator("span:has-text('Voir l\\'offre')").locator("..").locator("a").first.get_attribute("href")

                if link and link.startswith("/"):
                    link = "https://www.meteojob.com" + link

                jobs.append({
                    "title": title,
                    "location": LOCATION,
                    "url": link,
                    "source": "Meteojob"
                })

                print(f"{i+1}. {title}")

            except Exception as e:
                print(f"Erreur sur offre {i+1} :", e)

        browser.close()

    # ----- Sauvegarde JSON -----
    with open("meteojob_jobs.json", "w", encoding="utf-8") as f:
        json.dump(
            jobs,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"{len(jobs)} offres sauvegardées dans meteojob_jobs.json")


if __name__ == "__main__":
    scrape_meteojob()