from bs4 import BeautifulSoup
from scrappers.model import JobType, Location
from scrappers.util import get_enum_from_job_type

_JOB_TYPE_CODE_MAP = {
    JobType.FULL_TIME: "F",
    JobType.PART_TIME: "P",
    JobType.INTERNSHIP: "I",
    JobType.CONTRACT: "C",
    JobType.TEMPORARY: "T",
}

def job_type_code(job_type: JobType) -> str:
    return _JOB_TYPE_CODE_MAP.get(job_type, "")


def _extract_criteria_block(soup: BeautifulSoup, label: str) -> str | None:
    header = soup.find(
        "h3",
        class_="description__job-criteria-subheader",
        string=lambda t: t and label in t,
    )

    if not header:
        return None

    value_tag = header.find_next_sibling(
        "span",
        class_="description__job-criteria-text description__job-criteria-text--criteria",
    )

    return value_tag.get_text(strip=True) if value_tag else None


def parse_job_type(soup: BeautifulSoup) -> list[JobType]:
    raw = _extract_criteria_block(soup, "Employment type")

    if not raw:
        return []

    normalized = raw.lower().replace("-", "")
    enum_value = get_enum_from_job_type(normalized)

    return [enum_value] if enum_value else []


def parse_job_level(soup: BeautifulSoup) -> str | None:
    return _extract_criteria_block(soup, "Seniority level")


def parse_company_industry(soup: BeautifulSoup) -> str | None:
    return _extract_criteria_block(soup, "Industries")


def is_job_remote(title: dict, description: str, location: Location) -> bool:
    keywords = ("remote", "work from home", "wfh")

    location_text = location.display_location()

    combined = " ".join(
    str(x) for x in [title, description, location_text]
    if x is not None
    ).lower()

    return any(k in combined for k in keywords)