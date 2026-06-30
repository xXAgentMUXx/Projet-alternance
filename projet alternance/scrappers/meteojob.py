from playwright.sync_api import sync_playwright
import json
import re
import sys
import os

MAX_RESULTS = 30


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


def scrape_meteojob(keyword=None, location=None, max_results=MAX_RESULTS):
    if not keyword or not location:
        prefs    = load_prefs()
        keyword  = keyword  or prefs.get("keyword")  or "alternance développeur"
        location = location or prefs.get("city")     or "Montpellier"

    jobs = []

    in_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER", "") == "1"

    with sync_playwright() as p:

        launch_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
        ]

        browser = p.chromium.launch(
            headless=True,
            slow_mo=100 if not in_docker else 0,
            args=launch_args,
        )

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        print(f"[Meteojob] Recherche : '{keyword}' à '{location}'", file=sys.stderr)

        try:
            page.goto(
                "https://www.meteojob.com/",
                wait_until="networkidle",
                timeout=60000,
            )
        except Exception as e:
            print(f"Erreur chargement page : {e}", file=sys.stderr)
            browser.close()
            print(json.dumps([]))
            return []

        try:
            page.locator("#tarteaucitronPersonalize2").click(timeout=3000)
            print("Cookies acceptés", file=sys.stderr)
        except Exception:
            print("Pas de popup cookies", file=sys.stderr)

        page.wait_for_timeout(1500)

        print("Remplissage formulaire...", file=sys.stderr)
        try:
            inputs = page.locator("input")
            inputs.nth(0).fill(keyword)
            inputs.nth(1).fill(location)
            page.keyboard.press("Enter")
        except Exception as e:
            print(f"Erreur formulaire : {e}", file=sys.stderr)
            browser.close()
            print(json.dumps([]))
            return []

        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        page.wait_for_timeout(3000)

        links = page.locator("a")
        seen  = set()

        for i in range(links.count()):
            try:
                link  = links.nth(i)
                title = link.inner_text().strip()
                href  = link.get_attribute("href")

                if not href or not re.search(r"/jobs/\d+", href):
                    continue
                if href in seen:
                    continue

                seen.add(href)

                if href.startswith("/"):
                    href = "https://www.meteojob.com" + href

                jobs.append({
                    "title":    title,
                    "company":  "",
                    "location": location,
                    "url":      href,
                    "source":   "Meteojob",
                    "type":     "offre",
                })

                print(f"{len(jobs)}. {title}", file=sys.stderr)

                if len(jobs) >= max_results:
                    break

            except Exception as e:
                print(f"Erreur extraction : {e}", file=sys.stderr)

        browser.close()

    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "meteojob_jobs.json"
    )
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    print(f"[Meteojob] {len(jobs)} offres trouvées", file=sys.stderr)
    print(json.dumps(jobs, ensure_ascii=False))
    return jobs


if __name__ == "__main__":
    keyword  = sys.argv[1] if len(sys.argv) > 1 else None
    location = sys.argv[2] if len(sys.argv) > 2 else None
    scrape_meteojob(keyword, location)