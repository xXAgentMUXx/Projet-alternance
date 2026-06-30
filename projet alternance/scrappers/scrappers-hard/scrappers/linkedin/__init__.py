from __future__ import annotations
import random
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, urlunparse, unquote
import regex as re
from bs4 import BeautifulSoup
from bs4.element import Tag
from scrappers.exception import LinkedInException
from scrappers.linkedin.constant import headers
from scrappers.linkedin.util import (
    is_job_remote,
    job_type_code,
    parse_job_type,
    parse_job_level,
    parse_company_industry,
)
from scrappers.model import (
    JobPost,
    Location,
    JobResponse,
    Country,
    Compensation,
    DescriptionFormat,
    Scraper,
    ScraperInput,
    Site,
)
from scrappers.util import (
    extract_emails_from_text,
    currency_parser,
    markdown_converter,
    plain_converter,
    create_session,
    remove_attributes,
    create_logger,
)

log = create_logger("LinkedIn")

RESULTS_PER_PAGE = 25
MAX_OFFSET = 1000
MIN_DELAY_SECONDS = 3
DELAY_JITTER_SECONDS = 4
JOB_DETAIL_TIMEOUT = 5
SEARCH_REQUEST_TIMEOUT = 10


class LinkedIn(Scraper):
    base_url = "https://www.linkedin.com"

    def __init__(
        self,
        proxies: list[str] | str | None = None,
        ca_cert: str | None = None,
        user_agent: str | None = None,
    ):
        super().__init__(Site.LINKEDIN, proxies=proxies, ca_cert=ca_cert)
        self.session = create_session(
            proxies=self.proxies,
            ca_cert=ca_cert,
            is_tls=False,
            has_retry=True,
            delay=5,
            clear_cookies=True,
        )
        self.session.headers.update(headers)
        self.scraper_input: ScraperInput | None = None
        self.country = "worldwide"
        self.direct_url_pattern = re.compile(r'(?<=\?url=)[^"]+')

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        self.scraper_input = scraper_input

        collected: list[JobPost] = []
        already_seen: set[str] = set()
        cursor = self._initial_cursor(scraper_input.offset)
        page_number = 0

        while self._should_keep_searching(len(collected), cursor):
            page_number += 1
            log.info(f"page de recherche {page_number}")

            html = self._fetch_search_page(cursor)
            if html is None:
                break

            cards = self._extract_job_cards(html)
            if not cards:
                break

            new_jobs_count = 0
            for card in cards:
                job_id = self._card_job_id(card)
                if job_id is None or job_id in already_seen:
                    continue
                already_seen.add(job_id)

                try:
                    job = self._build_job_post(card, job_id, scraper_input.linkedin_fetch_description)
                except Exception as exc:
                    raise LinkedInException(str(exc))

                if job is not None:
                    collected.append(job)
                    new_jobs_count += 1

                if not self._should_keep_searching(len(collected), cursor):
                    break

            if self._should_keep_searching(len(collected), cursor):
                self._wait_between_requests()
                cursor += len(cards)

        return JobResponse(jobs=collected[: scraper_input.results_wanted])

    @staticmethod
    def _initial_cursor(offset: int | None) -> int:
        if not offset:
            return 0
        return (offset // RESULTS_PER_PAGE) * RESULTS_PER_PAGE

    def _should_keep_searching(self, found_so_far: int, cursor: int) -> bool:
        wanted = self.scraper_input.results_wanted
        return found_so_far < wanted and cursor < MAX_OFFSET

    def _build_search_params(self, cursor: int) -> dict:
        si = self.scraper_input
        seconds_old = si.hours_old * 3600 if si.hours_old else None

        raw_params = {
            "keywords": si.search_term,
            "location": si.location,
            "distance": si.distance,
            "f_WT": 2 if si.is_remote else None,
            "f_JT": job_type_code(si.job_type) if si.job_type else None,
            "pageNum": 0,
            "start": cursor,
            "f_AL": "true" if si.easy_apply else None,
            "f_C": (
                ",".join(map(str, si.linkedin_company_ids))
                if si.linkedin_company_ids
                else None
            ),
        }
        if seconds_old is not None:
            raw_params["f_TPR"] = f"r{seconds_old}"

        return {k: v for k, v in raw_params.items() if v is not None}

    def _fetch_search_page(self, cursor: int) -> str | None:
        endpoint = f"{self.base_url}/jobs-guest/jobs/api/seeMoreJobPostings/search?"
        params = self._build_search_params(cursor)

        try:
            response = self.session.get(endpoint, params=params, timeout=SEARCH_REQUEST_TIMEOUT)
        except Exception as exc:
            if "Proxy responded with" in str(exc):
                log.error("LinkedIn : proxy invalide")
            else:
                log.error(f"LinkedIn : {exc}")
            return None

        if response.status_code not in range(200, 400):
            if response.status_code == 429:
                log.error("LinkedIn a bloqué la requête (429 — trop de requêtes)")
            else:
                log.error(f"LinkedIn a répondu {response.status_code} : {response.text}")
            return None

        return response.text

    def _wait_between_requests(self):
        pause = random.uniform(MIN_DELAY_SECONDS, MIN_DELAY_SECONDS + DELAY_JITTER_SECONDS)
        time.sleep(pause)

    @staticmethod
    def _extract_job_cards(html: str) -> list[Tag]:
        soup = BeautifulSoup(html, "html.parser")
        return soup.find_all("div", class_="base-search-card")

    @staticmethod
    def _card_job_id(card: Tag) -> str | None:
        link_tag = card.find("a", class_="base-card__full-link")
        if not link_tag or "href" not in link_tag.attrs:
            return None
        clean_href = link_tag.attrs["href"].split("?")[0]
        return clean_href.split("-")[-1]

    def _build_job_post(self, card: Tag, job_id: str, fetch_full_description: bool) -> Optional[JobPost]:
        compensation = self._parse_compensation(card)
        title = self._parse_title(card)
        company_name, company_url = self._parse_company(card)
        metadata = card.find("div", class_="base-search-card__metadata")
        location = self._parse_location(metadata)
        date_posted = self._parse_date(metadata)

        details: dict = {}
        if fetch_full_description:
            details = self._fetch_job_detail_page(job_id)

        description = details.get("description")
        remote_flag = is_job_remote(title, description, location)

        return JobPost(
            id=f"li-{job_id}",
            title=title,
            company_name=company_name,
            company_url=company_url,
            location=location,
            is_remote=remote_flag,
            date_posted=date_posted,
            job_url=f"{self.base_url}/jobs/view/{job_id}",
            compensation=compensation,
            job_type=details.get("job_type"),
            job_level=(details.get("job_level") or "").lower(),
            company_industry=details.get("company_industry"),
            description=description,
            job_url_direct=details.get("job_url_direct"),
            emails=extract_emails_from_text(description),
            company_logo=details.get("company_logo"),
            job_function=details.get("job_function"),
        )

    @staticmethod
    def _parse_title(card: Tag) -> str:
        title_tag = card.find("span", class_="sr-only")
        return title_tag.get_text(strip=True) if title_tag else "N/A"

    @staticmethod
    def _parse_company(card: Tag) -> tuple[str, str]:
        subtitle = card.find("h4", class_="base-search-card__subtitle")
        link = subtitle.find("a") if subtitle else None

        name = link.get_text(strip=True) if link else "N/A"
        url = ""
        if link and link.has_attr("href"):
            url = urlunparse(urlparse(link.get("href"))._replace(query=""))

        return name, url

    @staticmethod
    def _parse_compensation(card: Tag) -> Compensation | None:
        salary_tag = card.find("span", class_="job-search-card__salary-info")
        if not salary_tag:
            return None

        salary_text = salary_tag.get_text(separator=" ").strip()
        bounds = [currency_parser(part) for part in salary_text.split("-")]
        currency_symbol = salary_text[0] if salary_text[0] != "$" else "USD"

        return Compensation(
            min_amount=int(bounds[0]),
            max_amount=int(bounds[1]),
            currency=currency_symbol,
        )

    @staticmethod
    def _parse_date(metadata: Optional[Tag]) -> datetime | None:
        if metadata is None:
            return None

        time_tag = metadata.find("time", class_="job-search-card__listdate")
        if time_tag is None:
            time_tag = metadata.find("time", class_="job-search-card__listdate--new")

        if time_tag is None or "datetime" not in time_tag.attrs:
            return None

        try:
            return datetime.strptime(time_tag["datetime"], "%Y-%m-%d")
        except ValueError:
            return None

    def _parse_location(self, metadata: Optional[Tag]) -> Location:
        default = Location(country=Country.from_string(self.country))
        if metadata is None:
            return default

        location_tag = metadata.find("span", class_="job-search-card__location")
        raw_text = location_tag.text.strip() if location_tag else "N/A"
        segments = raw_text.split(", ")

        if len(segments) == 2:
            city, state = segments
            return Location(city=city, state=state, country=Country.from_string(self.country))

        if len(segments) == 3:
            city, state, country_name = segments
            return Location(city=city, state=state, country=Country.from_string(country_name))

        return default

    def _fetch_job_detail_page(self, job_id: str) -> dict:
        try:
            response = self.session.get(f"{self.base_url}/jobs/view/{job_id}", timeout=JOB_DETAIL_TIMEOUT)
            response.raise_for_status()
        except Exception:
            return {}

        if "linkedin.com/signup" in response.url:
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        return {
            "description": self._extract_description(soup),
            "job_level": parse_job_level(soup),
            "company_industry": parse_company_industry(soup),
            "job_type": parse_job_type(soup),
            "job_url_direct": self._extract_direct_url(soup),
            "company_logo": self._extract_company_logo(soup),
            "job_function": self._extract_job_function(soup),
        }

    def _extract_description(self, soup: BeautifulSoup) -> str | None:
        container = soup.find("div", class_=lambda x: x and "show-more-less-html__markup" in x)
        if container is None:
            return None

        cleaned = remove_attributes(container)
        rendered = cleaned.prettify(formatter="html")

        fmt = self.scraper_input.description_format
        if fmt == DescriptionFormat.MARKDOWN:
            return markdown_converter(rendered)
        if fmt == DescriptionFormat.PLAIN:
            return plain_converter(rendered)
        return rendered

    @staticmethod
    def _extract_job_function(soup: BeautifulSoup) -> str | None:
        heading = soup.find("h3", text=lambda t: t and "Job function" in t.strip())
        if heading is None:
            return None
        value_span = heading.find_next("span", class_="description__job-criteria-text")
        return value_span.text.strip() if value_span else None

    @staticmethod
    def _extract_company_logo(soup: BeautifulSoup) -> str | None:
        logo = soup.find("img", {"class": "artdeco-entity-image"})
        return logo.get("data-delayed-url") if logo else None

    def _extract_direct_url(self, soup: BeautifulSoup) -> str | None:
        apply_code = soup.find("code", id="applyUrl")
        if not apply_code:
            return None

        match = self.direct_url_pattern.search(apply_code.decode_contents().strip())
        return unquote(match.group()) if match else None