from time import time
import common as jc
from scraping.jobs import scraping_jobs


class scraping_jobs_apec(scraping_jobs):

    CONTRACT_CODES = {
        "perm": "101888",
        "full": "101888",
        "ints": "20053",
        "free": "101887",
    }

    def set_code_dpt(self, department_code):
        self.code_dpt = department_code

    def _build_payload(self, page_index):
        return {
            "lieux": [self.code_dpt],
            "typeClient": "CADRE",
            "sorts": [
                {
                    "type": "SCORE",
                    "direction": "DESCENDING",
                }
            ],
            "pagination": {
                "range": 20,
                "startIndex": page_index,
            },
            "activeFiltre": True,
            "pointGeolocDeReference": {
                "distance": 0,
            },
            "motsCles": self.s_job,
        }

    @staticmethod
    def _format_job(job):
        return {
            "title": job["intitule"],
            "link": (
                "https://www.apec.fr/candidat/recherche-emploi.html/"
                f"emploi/detail-offre/{job['numeroOffre']}"
            ),
            "location": job["lieuTexte"],
            "description": job["texteOffre"],
            "company": job["nomCommercial"],
            "note": job["score"],
            "salary": job["salaireTexte"],
            "publication_date": job["datePublication"],
            "publication_time": "",
        }

    def scrap_job(self):
        endpoint = "https://www.apec.fr/cms/webservices/rechercheOffre"

        # Conserve la logique d'origine
        if (
            self.type_contract
            and self.type_contract in self.CONTRACT_CODES
        ):
            _ = 597171

        collected_jobs = []
        request_count = 0
        started_at = time()

        for page in range(jc.NB_PAGE):
            payload = self._build_payload(page)

            response = jc.post_data(
                endpoint,
                payload,
                request_count,
                started_at,
            )

            offers = response.get("resultats", [])

            for offer in offers:
                collected_jobs.append(self._format_job(offer))

        return collected_jobs