"""
Usage :
    py linkedin_message.py <profile_url> "<message>"
    py linkedin_message.py https://www.linkedin.com/in/john-doe "Bonjour, ..."
"""

import sys
import pickle
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

SESSION_FILE = "session.pkl"

def load_cookies(session_file: str) -> list[dict]:
    """
    Charge le fichier session.pkl de StaffSpy et convertit les cookies
    au format Playwright.
    """
    path = Path(session_file)
    if not path.exists():
        raise FileNotFoundError(
            f"Session introuvable : {session_file}\n"
            "Lance d'abord StaffSpy pour créer la session (connexion LinkedIn)."
        )

    with open(path, "rb") as f:
        raw = pickle.load(f)

    cookies = []

    if hasattr(raw, "items"):
        for name, value in raw.items():
            cookies.append({
                "name":   name,
                "value":  value,
                "domain": ".linkedin.com",
                "path":   "/",
            })
    elif isinstance(raw, list):
        for c in raw:
            if isinstance(c, dict):
                cookies.append({
                    "name":   c.get("name", ""),
                    "value":  c.get("value", ""),
                    "domain": c.get("domain", ".linkedin.com"),
                    "path":   c.get("path", "/"),
                })

    if not cookies:
        raise ValueError(
            "Session vide ou format non reconnu. "
            "Supprime session.pkl et relance StaffSpy pour régénérer."
        )

    print(f"  Session chargée : {len(cookies)} cookies")
    return cookies

def open_message(profile_url: str, message: str, headless: bool = False):
    """
    1. Ouvre LinkedIn avec les cookies de session
    2. Navigue sur le profil cible
    3. Clique sur "Envoyer un message" / "Message"
    4. Pré-remplit le champ message
    5. N'envoie PAS — attend que l'utilisateur valide manuellement
    """
    cookies = load_cookies(SESSION_FILE)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=300,
            args=["--start-maximized"],
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )

        context.add_cookies(cookies)
        page = context.new_page()

        print("Vérification de la session...")
        page.goto("https://www.linkedin.com/feed/", timeout=30_000)
        page.wait_for_load_state("networkidle")

        if "login" in page.url or "authwall" in page.url:
            print("Session expirée — reconnecte-toi via StaffSpy pour régénérer session.pkl")
            browser.close()
            return

        print("Session valide")

        print(f"Navigation vers : {profile_url}")
        page.goto(profile_url, timeout=30_000)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        MESSAGE_SELECTORS = [
            "button:has-text('Message')",
            "button:has-text('Envoyer un message')",
            "a:has-text('Message')",
            "[aria-label*='Envoyer un message']",
            "[aria-label*='Message']",
            "button.message-anywhere-button",
        ]

        clicked = False
        for selector in MESSAGE_SELECTORS:
            try:
                btn = page.locator(selector).first
                btn.wait_for(timeout=3_000)
                btn.click()
                print(f"  Bouton trouvé : {selector}")
                clicked = True
                break
            except PlaywrightTimeout:
                continue

        if not clicked:
            print(
                "Bouton 'Message' introuvable.\n"
                "   Causes possibles :\n"
                "   - Le profil n'est pas une connexion (LinkedIn bloque les messages hors réseau)\n"
                "   - Le profil a désactivé les messages\n"
                "   - La page n'a pas fini de charger\n"
                "   Le navigateur reste ouvert pour inspection."
            )
            input("Appuie sur Entrée pour fermer...")
            browser.close()
            return

        page.wait_for_timeout(2_000)

        TEXTAREA_SELECTORS = [
            "div[role='textbox'][contenteditable='true']",
            "div.msg-form__contenteditable",
            "div[aria-label*='Message']",
            "div[aria-label*='Écrire']",
            "textarea.msg-form__textarea",
        ]

        typed = False
        for selector in TEXTAREA_SELECTORS:
            try:
                box = page.locator(selector).first
                box.wait_for(timeout=4_000)
                box.click()
                box.fill("")          # vide d'abord
                page.keyboard.type(message, delay=30)
                print(f"  Message pré-rempli ({len(message)} caractères)")
                typed = True
                break
            except PlaywrightTimeout:
                continue

        if not typed:
            print(
                "Champ message introuvable.\n"
                "Essaie de cliquer manuellement dans la boîte de dialogue.")

        # ── Étape 5 : attente manuelle avant envoi ────────
        print("\n" + "─" * 55)
        print("Message pré-rempli dans la messagerie LinkedIn.")
        print("Vérifie le message dans le navigateur.")
        print("Clique sur Envoyer si tu valides.")
        print("Le script N'ENVOIE PAS automatiquement.")
        print("─" * 55)
        input("\nAppuie sur Entrée ici pour fermer le navigateur...")

        browser.close()
        print("Navigateur fermé.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage : py linkedin_message.py <profile_url> \"<message>\"\n"
            "Ex    : py linkedin_message.py "
            "https://www.linkedin.com/in/john-doe \"Bonjour John, ...\""
        )
        sys.exit(1)

    profile_url = sys.argv[1]
    message     = sys.argv[2]

    print(f"\nProfil  : {profile_url}")
    print(f"Message : {message[:60]}{'...' if len(message) > 60 else ''}\n")

    open_message(profile_url, message)