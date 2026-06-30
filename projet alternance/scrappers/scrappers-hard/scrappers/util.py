from __future__ import annotations
import logging
import re
from itertools import cycle
import numpy as np
import requests
import tls_client
import urllib3
from markdownify import markdownify as md
from requests.adapters import HTTPAdapter, Retry
from scrappers.model import CompensationInterval, JobType, Site
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_logger(scope_name: str):
    log = logging.getLogger(f"JobSpy:{scope_name}")
    log.propagate = False
    if not log.handlers:
        log.setLevel(logging.INFO)
        stream_handler = logging.StreamHandler()
        fmt = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        stream_handler.setFormatter(logging.Formatter(fmt))
        log.addHandler(stream_handler)
    return log
create_logger = build_logger


class _ProxyRotatorMixin:
    def __init__(self, proxies=None):
        if isinstance(proxies, str):
            self._proxy_pool = cycle([self._to_proxy_dict(proxies)])
        elif isinstance(proxies, list):
            self._proxy_pool = (
                cycle([self._to_proxy_dict(p) for p in proxies]) if proxies else None
            )
        else:
            self._proxy_pool = None

    @staticmethod
    def _to_proxy_dict(proxy_value: str) -> dict:
        if proxy_value.startswith(("http://", "https://", "socks5://")):
            return {"http": proxy_value, "https": proxy_value}
        return {"http": f"http://{proxy_value}", "https": f"http://{proxy_value}"}


class RequestsRotating(_ProxyRotatorMixin, requests.Session):
    def __init__(self, proxies=None, has_retry=False, delay=1, clear_cookies=False):
        _ProxyRotatorMixin.__init__(self, proxies=proxies)
        requests.Session.__init__(self)
        self.clear_cookies = clear_cookies
        self.allow_redirects = True
        self._configure_retries(has_retry, delay)

    def _configure_retries(self, has_retry: bool, delay: int):
        if not has_retry:
            return
        retry_policy = Retry(
            total=3,
            connect=3,
            status=3,
            status_forcelist=[500, 502, 503, 504, 429],
            backoff_factor=delay,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

    def request(self, method, url, **kwargs):
        if self.clear_cookies:
            self.cookies.clear()

        if self._proxy_pool:
            chosen = next(self._proxy_pool)
            self.proxies = {} if chosen["http"] == "http://localhost" else chosen

        return requests.Session.request(self, method, url, **kwargs)


class TLSRotating(_ProxyRotatorMixin, tls_client.Session):
    def __init__(self, proxies=None):
        _ProxyRotatorMixin.__init__(self, proxies=proxies)
        tls_client.Session.__init__(self, random_tls_extension_order=True)

    def execute_request(self, *args, **kwargs):
        if self._proxy_pool:
            chosen = next(self._proxy_pool)
            self.proxies = {} if chosen["http"] == "http://localhost" else chosen

        resp = tls_client.Session.execute_request(self, *args, **kwargs)
        resp.ok = resp.status_code in range(200, 400)
        return resp


def create_session(
    *,
    proxies: dict | str | None = None,
    ca_cert: str | None = None,
    is_tls: bool = True,
    has_retry: bool = False,
    delay: int = 1,
    clear_cookies: bool = False,
) -> requests.Session:
    if is_tls:
        http_session = TLSRotating(proxies=proxies)
    else:
        http_session = RequestsRotating(
            proxies=proxies,
            has_retry=has_retry,
            delay=delay,
            clear_cookies=clear_cookies,
        )

    if ca_cert:
        http_session.verify = ca_cert

    return http_session


_VERBOSITY_TO_LEVEL = {2: "INFO", 1: "WARNING", 0: "ERROR"}


def set_logger_level(verbose: int):
    if verbose is None:
        return

    level_name = _VERBOSITY_TO_LEVEL.get(verbose, "INFO")
    level = getattr(logging, level_name, None)
    if level is None:
        raise ValueError(f"Invalid log level: {level_name}")

    for existing_name in logging.root.manager.loggerDict:
        if existing_name.startswith("JobSpy:"):
            logging.getLogger(existing_name).setLevel(level)


def markdown_converter(description_html: str):
    if description_html is None:
        return None
    return md(description_html).strip()


def plain_converter(description_html: str):
    from bs4 import BeautifulSoup

    if description_html is None:
        return None

    soup = BeautifulSoup(description_html, "html.parser")
    raw_text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", raw_text).strip()


_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def extract_emails_from_text(text: str) -> list[str] | None:
    if not text:
        return None
    return _EMAIL_PATTERN.findall(text)


def get_enum_from_job_type(job_type_str: str) -> JobType | None:
    matched = None
    for candidate in JobType:
        if job_type_str in candidate.value:
            matched = candidate
    return matched


def currency_parser(cur_str: str):
    cleaned = re.sub("[^-0-9.,]", "", cur_str)
    cleaned = re.sub("[.,]", "", cleaned[:-3]) + cleaned[-3:]

    tail = cleaned[-3:]
    if "." in tail:
        amount = float(cleaned)
    elif "," in tail:
        amount = float(cleaned.replace(",", "."))
    else:
        amount = float(cleaned)

    return np.round(amount, 2)


def remove_attributes(tag):
    for attr_name in list(tag.attrs):
        del tag[attr_name]
    return tag


def extract_salary(
    salary_str,
    lower_limit=1000,
    upper_limit=700000,
    hourly_threshold=350,
    monthly_threshold=30000,
    enforce_annual_salary=False,
):
    if not salary_str:
        return None, None, None, None

    annual_max = None
    range_pattern = (
        r"\$(\d+(?:,\d+)?(?:\.\d+)?)([kK]?)\s*[-—–]\s*(?:\$)?"
        r"(\d+(?:,\d+)?(?:\.\d+)?)([kK]?)"
    )

    def to_int(raw: str) -> int:
        return int(float(raw.replace(",", "")))

    def hourly_to_annual(wage: float) -> float:
        return wage * 2080

    def monthly_to_annual(wage: float) -> float:
        return wage * 12

    match = re.search(range_pattern, salary_str)
    if not match:
        return None, None, None, None

    min_val = to_int(match.group(1))
    max_val = to_int(match.group(3))

    if "k" in match.group(2).lower() or "k" in match.group(4).lower():
        min_val *= 1000
        max_val *= 1000

    if min_val < hourly_threshold:
        period = CompensationInterval.HOURLY.value
        annual_min = hourly_to_annual(min_val)
        if max_val < hourly_threshold:
            annual_max = hourly_to_annual(max_val)
    elif min_val < monthly_threshold:
        period = CompensationInterval.MONTHLY.value
        annual_min = monthly_to_annual(min_val)
        if max_val < monthly_threshold:
            annual_max = monthly_to_annual(max_val)
    else:
        period = CompensationInterval.YEARLY.value
        annual_min = min_val
        annual_max = max_val

    if not annual_max:
        return None, None, None, None

    in_range = (
        lower_limit <= annual_min <= upper_limit
        and lower_limit <= annual_max <= upper_limit
        and annual_min < annual_max
    )
    if not in_range:
        return None, None, None, None

    if enforce_annual_salary:
        return period, annual_min, annual_max, "USD"
    return period, min_val, max_val, "USD"


_JOB_TYPE_PATTERNS = {
    JobType.FULL_TIME: r"full\s?time",
    JobType.PART_TIME: r"part\s?time",
    JobType.INTERNSHIP: r"internship",
    JobType.CONTRACT: r"contract",
}


def extract_job_type(description: str):
    if not description:
        return []

    found = [
        job_type
        for job_type, pattern in _JOB_TYPE_PATTERNS.items()
        if re.search(pattern, description, re.IGNORECASE)
    ]
    return found if found else None


def map_str_to_site(site_name: str) -> Site:
    return Site[site_name.upper()]


def get_enum_from_value(value_str):
    for job_type in JobType:
        if value_str in job_type.value:
            return job_type
    raise Exception(f"Invalid job type: {value_str}")


_ANNUALIZATION_FACTORS = {
    "hourly": 2080,
    "monthly": 12,
    "weekly": 52,
    "daily": 260,
}


def convert_to_annual(job_data: dict):
    """Convertit min_amount/max_amount vers une base annuelle, en place."""
    factor = _ANNUALIZATION_FACTORS.get(job_data["interval"])
    if factor:
        job_data["min_amount"] *= factor
        job_data["max_amount"] *= factor
    job_data["interval"] = "yearly"


desired_order = [
    "id",
    "site",
    "job_url",
    "job_url_direct",
    "title",
    "company",
    "location",
    "date_posted",
    "job_type",
    "salary_source",
    "interval",
    "min_amount",
    "max_amount",
    "currency",
    "is_remote",
    "job_level",
    "job_function",
    "listing_type",
    "emails",
    "description",
    "company_industry",
    "company_url",
    "company_logo",
    "company_url_direct",
    "company_addresses",
    "company_num_employees",
    "company_revenue",
    "company_description",
    "skills",
    "experience_range",
    "company_rating",
    "company_reviews_count",
    "vacancy_count",
    "work_from_home_type",
]