from __future__ import annotations
import math
from datetime import datetime
from typing import Tuple
from scrappers.indeed.constant import job_search_query, api_headers
from scrappers.indeed.util import is_job_remote, get_compensation, get_job_type
from scrappers.model import (
    Scraper,
    ScraperInput,
    Site,
    JobPost,
    Location,
    JobResponse,
    JobType,
    DescriptionFormat,
)
from scrappers.util import (
    extract_emails_from_text,
    markdown_converter,
    create_session,
    create_logger,
)

log = create_logger("Indeed")

PAGE_SIZE = 100
REQUEST_TIMEOUT = 10

JOB_TYPE_ATTRIBUTE_CODES = {
    JobType.FULL_TIME:  "CF3CP",
    JobType.PART_TIME:  "75GKK",
    JobType.CONTRACT:   "NJXCK",
    JobType.INTERNSHIP: "VDTG7",
}
REMOTE_ATTRIBUTE_CODE = "DSQF7"


class Indeed(Scraper):

    api_url = "https://apis.indeed.com/graphql"

    def __init__(
        self,
        proxies: list[str] | str | None = None,
        ca_cert: str | None = None,
        user_agent: str | None = None,
    ):
        super().__init__(Site.INDEED, proxies=proxies)

        self.session = create_session(proxies=self.proxies, ca_cert=ca_cert, is_tls=False)
        self.scraper_input: ScraperInput | None = None
        self.seen_urls: set[str] = set()
        self.country_code: str | None = None
        self.base_url: str | None = None

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        self.scraper_input = scraper_input
        self._configure_country()

        target_total = scraper_input.results_wanted + scraper_input.offset
        collected: list[JobPost] = []
        cursor: str | None = None
        page = 1

        while len(self.seen_urls) < target_total:
            total_pages_estimate = math.ceil(scraper_input.results_wanted / PAGE_SIZE)
            log.info(f"page {page} / {total_pages_estimate}")

            page_jobs, cursor = self._fetch_page(cursor)
            if not page_jobs:
                log.info(f"aucune offre trouvée page {page}")
                break

            collected.extend(page_jobs)
            page += 1

        start = scraper_input.offset
        end = start + scraper_input.results_wanted
        return JobResponse(jobs=collected[start:end])

    def _configure_country(self):
        domain, self.country_code = self.scraper_input.country.indeed_domain_value
        self.base_url = f"https://{domain}.indeed.com"

    def _request_headers(self) -> dict:
        headers = api_headers.copy()
        headers["indeed-co"] = self.country_code
        return headers

    def _fetch_page(self, cursor: str | None) -> Tuple[list[JobPost], str | None]:
        query = self._build_graphql_query(cursor)

        try:
            response = self.session.post(
                self.api_url,
                headers=self._request_headers(),
                json={"query": query},
                timeout=REQUEST_TIMEOUT,
                verify=False,
            )
        except Exception as exc:
            log.info(f"erreur réseau Indeed : {exc}")
            return [], None

        if not response.ok:
            log.info(f"Indeed a répondu avec le code {response.status_code}")
            return [], None

        payload = response.json()
        search_results = payload["data"]["jobSearch"]
        next_cursor = search_results["pageInfo"]["nextCursor"]

        jobs: list[JobPost] = []
        for entry in search_results["results"]:
            job = self._convert_to_job_post(entry["job"])
            if job is not None:
                jobs.append(job)

        return jobs, next_cursor

    def _build_graphql_query(self, cursor: str | None) -> str:
        si = self.scraper_input
        search_term = (si.search_term or "").replace('"', '\\"')

        what_clause = f'what: "{search_term}"' if search_term else ""
        location_clause = (
            f'location: {{where: "{si.location}", radius: {si.distance}, radiusUnit: MILES}}'
            if si.location
            else ""
        )
        cursor_clause = f'cursor: "{cursor}"' if cursor else ""

        return job_search_query.format(
            what=what_clause,
            location=location_clause,
            dateOnIndeed=si.hours_old,
            cursor=cursor_clause,
            filters=self._build_filters_clause(),
        )

    def _build_filters_clause(self) -> str:
        si = self.scraper_input

        if si.hours_old:
            return f"""
            filters: {{
                date: {{
                  field: "dateOnIndeed",
                  start: "{si.hours_old}h"
                }}
            }}
            """

        if si.easy_apply:
            return """
            filters: {
                keyword: {
                  field: "indeedApplyScope",
                  keys: ["DESKTOP"]
                }
            }
            """

        if si.job_type or si.is_remote:
            keys = self._attribute_keys_for(si)
            if keys:
                joined_keys = '", "'.join(keys)
                return f"""
                filters: {{
                  composite: {{
                    filters: [{{
                      keyword: {{
                        field: "attributes",
                        keys: ["{joined_keys}"]
                      }}
                    }}]
                  }}
                }}
                """

        return ""

    @staticmethod
    def _attribute_keys_for(si: ScraperInput) -> list[str]:
        keys: list[str] = []
        if si.job_type:
            keys.append(JOB_TYPE_ATTRIBUTE_CODES[si.job_type])
        if si.is_remote:
            keys.append(REMOTE_ATTRIBUTE_CODE)
        return keys

    def _convert_to_job_post(self, job: dict) -> JobPost | None:
        job_url = f'{self.base_url}/viewjob?jk={job["key"]}'
        if job_url in self.seen_urls:
            return None
        self.seen_urls.add(job_url)

        description = self._extract_description(job)
        employer_info = self._extract_employer_info(job)

        return JobPost(
            id=f'in-{job["key"]}',
            title=job["title"],
            description=description,
            company_name=employer_info["name"],
            company_url=employer_info["page_url"],
            company_url_direct=employer_info["website_url"],
            location=self._extract_location(job),
            job_type=get_job_type(job["attributes"]),
            compensation=get_compensation(job["compensation"]),
            date_posted=self._extract_date_posted(job),
            job_url=job_url,
            job_url_direct=self._extract_direct_apply_url(job),
            emails=extract_emails_from_text(description) if description else None,
            is_remote=is_job_remote(job, description),
            company_addresses=employer_info["address"],
            company_industry=employer_info["industry"],
            company_num_employees=employer_info["employee_count_label"],
            company_revenue=employer_info["revenue_label"],
            company_description=employer_info["brief_description"],
            company_logo=employer_info["logo_url"],
        )

    def _extract_description(self, job: dict) -> str:
        raw_html = job["description"]["html"]
        if self.scraper_input.description_format == DescriptionFormat.MARKDOWN:
            return markdown_converter(raw_html)
        return raw_html

    @staticmethod
    def _extract_date_posted(job: dict) -> str:
        timestamp = job["datePublished"] / 1000
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

    @staticmethod
    def _extract_location(job: dict) -> Location:
        loc = job.get("location", {})
        return Location(
            city=loc.get("city"),
            state=loc.get("admin1Code"),
            country=loc.get("countryCode"),
        )

    @staticmethod
    def _extract_direct_apply_url(job: dict) -> str | None:
        recruit = job.get("recruit")
        return recruit.get("viewJobUrl") if recruit else None

    def _extract_employer_info(self, job: dict) -> dict:
        employer = job.get("employer")
        if not employer:
            return {
                "name": None, "page_url": None, "website_url": None,
                "address": None, "industry": None,
                "employee_count_label": None, "revenue_label": None,
                "brief_description": None, "logo_url": None,
            }

        details = employer.get("dossier", {}).get("employerDetails", {}) if employer.get("dossier") else {}
        relative_url = job.get("employer", {}).get("relativeCompanyPageUrl")
        addresses = details.get("addresses")
        industry_raw = details.get("industry")
        images = employer.get("images")

        return {
            "name":               employer.get("name"),
            "page_url":           f"{self.base_url}{relative_url}" if relative_url else None,
            "website_url":        details.get("links", {}).get("corporateWebsite") if details else None,
            "address":            addresses[0] if addresses else None,
            "industry":           self._format_industry_label(industry_raw),
            "employee_count_label": details.get("employeesLocalizedLabel"),
            "revenue_label":       details.get("revenueLocalizedLabel"),
            "brief_description":   details.get("briefDescription"),
            "logo_url":            images.get("squareLogoUrl") if images else None,
        }

    @staticmethod
    def _format_industry_label(raw: str | None) -> str | None:
        if not raw:
            return None
        return raw.replace("Iv1", "").replace("_", " ").title().strip()