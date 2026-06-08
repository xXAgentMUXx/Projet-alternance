from staffspy import LinkedInAccount

account = LinkedInAccount(
    session_file="session.pkl",
    log_level=1,
)

staff = account.scrape_staff(
    company_name="Capgemini",
    search_term="RH",
    location="Montpellier",
    max_results=50,
)

staff.to_csv("openai.csv", index=False)

print(staff.head())
print(f"{len(staff)} profils récupérés")