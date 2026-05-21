from playwright.sync_api import sync_playwright
import json
import time
import os

MAX_RESULTS = 10000

KEYWORDS = [
    "recruiter",
    "talent",
    "hr",
    "rh",
    "manager"
]

LOCATIONS = [
    "montpellier",
    "lattes",
    "occitanie"
]


def is_logged(page):
    return "feed" in page.url or "linkedin.com/in/" in page.url


def scrape_people(company_url):

    people_url = company_url.rstrip("/") + "/people"
    all_profiles = {}

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        # utilise la session sauvegardée
        if os.path.exists("linkedin_session.json"):
            context = browser.new_context(
                storage_state="linkedin_session.json"
            )
            print("Session chargée")
        else:
            context = browser.new_context()
            print("Pas de session trouvée")

        page = context.new_page()

        # aller sur linkedin home d'abord
        page.goto(
            "https://www.linkedin.com/feed/",
            timeout=120000
        )

        time.sleep(5)

        # si pas connecté
        if not is_logged(page):
            print("Connexion nécessaire...")
            page.goto(
                "https://www.linkedin.com/login"
            )

            input(
                "Connecte-toi puis ENTER"
            )

            # sauvegarde session
            context.storage_state(
                path="linkedin_session.json"
            )
            print("Session sauvegardée")

        # page people
        page.goto(
            people_url,
            timeout=120000
        )

        time.sleep(5)

        for keyword in KEYWORDS:

            print(f"\nRecherche: {keyword}")

            try:
                search = page.locator(
                    'input[placeholder*="Search employees"]'
                )

                search.fill("")
                search.fill(keyword)

                page.keyboard.press("Enter")

                time.sleep(4)

            except:
                print("Barre de recherche introuvable")
                continue

            while True:

                cards = page.locator(
                    ".org-people-profile-card"
                )

                count = cards.count()

                print("Profils page:", count)

                for i in range(count):

                    try:
                        card = cards.nth(i)

                        name = card.locator(
                            ".artdeco-entity-lockup__title"
                        ).inner_text()

                        role = card.locator(
                            ".artdeco-entity-lockup__subtitle"
                        ).inner_text()

                        profile_url = card.locator(
                            "a"
                        ).first.get_attribute("href")

                        full_text = (
                            card.inner_text()
                            .lower()
                        )

                        if any(
                            loc in full_text
                            for loc in LOCATIONS
                        ):
                            all_profiles[
                                profile_url
                            ] = {
                                "name": name,
                                "role": role,
                                "url": profile_url
                            }

                    except:
                        pass

                    if len(all_profiles) >= MAX_RESULTS:
                        break

                if len(all_profiles) >= MAX_RESULTS:
                    break

                next_btn = page.locator(
                    ".artdeco-pagination__button--next"
                )

                if (
                    next_btn.count() == 0
                    or next_btn.is_disabled()
                ):
                    break

                next_btn.click()
                time.sleep(4)

        context.close()
        browser.close()

    final = list(all_profiles.values())

    with open(
        "linkedin_people.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            final,
            f,
            indent=4,
            ensure_ascii=False
        )

    print("Total:", len(final))


if __name__ == "__main__":
    company = input(
        "URL company LinkedIn: "
    )

    scrape_people(company)