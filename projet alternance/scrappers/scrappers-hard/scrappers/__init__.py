from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple

import pandas as pd

from scrappers.indeed import Indeed
from scrappers.linkedin import LinkedIn
from scrappers.model import JobType, Location, JobResponse, Country
from scrappers.model import SalarySource, ScraperInput, Site
from scrappers.util import (
    set_logger_level,
    extract_salary,
    create_logger,
    get_enum_from_value,
    map_str_to_site,
    convert_to_annual,
    desired_order,
)

_PLATFORM_SCRAPERS = {
    Site.LINKEDIN: LinkedIn,
    Site.INDEED: Indeed,
}

_DISPLAY_NAME_OVERRIDES = {
    "Zip_recruiter": "ZipRecruiter",
    "Linkedin": "LinkedIn",
}


def _resolve_site_targets(site_name) -> list[Site]:
    if isinstance(site_name, str):
        return [map_str_to_site(site_name)]
    if isinstance(site_name, Site):
        return [site_name]
    if isinstance(site_name, list):
        return [
            map_str_to_site(entry) if isinstance(entry, str) else entry
            for entry in site_name
        ]
    return list(Site)


def _platform_display_name(site: Site) -> str:
    capitalized = site.value.capitalize()
    return _DISPLAY_NAME_OVERRIDES.get(capitalized, capitalized)


def _run_single_platform(
    site: Site, scraper_input: ScraperInput, proxies, ca_cert, user_agent
) -> Tuple[str, JobResponse]:
    scraper_cls = _PLATFORM_SCRAPERS[site]
    scraper_instance = scraper_cls(proxies=proxies, ca_cert=ca_cert, user_agent=user_agent)
    response: JobResponse = scraper_instance.scrape(scraper_input)

    create_logger(_platform_display_name(site)).info("finished scraping")
    return site.value, response


def _apply_compensation_fields(job_data: dict, country: Country, enforce_annual: bool):
    compensation = job_data.get("compensation")

    if compensation and isinstance(compensation, dict):
        job_data["interval"] = (
            compensation.get("interval").value if compensation.get("interval") else None
        )
        job_data["min_amount"] = compensation.get("min_amount")
        job_data["max_amount"] = compensation.get("max_amount")
        job_data["currency"] = compensation.get("currency", "USD")
        job_data["salary_source"] = SalarySource.DIRECT_DATA.value

        needs_conversion = (
            enforce_annual
            and job_data["interval"]
            and job_data["interval"] != "yearly"
            and job_data["min_amount"]
            and job_data["max_amount"]
        )
        if needs_conversion:
            convert_to_annual(job_data)

    elif country == Country.USA:
        (
            job_data["interval"],
            job_data["min_amount"],
            job_data["max_amount"],
            job_data["currency"],
        ) = extract_salary(job_data["description"], enforce_annual_salary=enforce_annual)
        job_data["salary_source"] = SalarySource.DESCRIPTION.value

    job_data["salary_source"] = (
        job_data["salary_source"]
        if "min_amount" in job_data and job_data["min_amount"]
        else None
    )


def _flatten_job_to_row(job, site_value: str, country: Country, enforce_annual: bool) -> pd.DataFrame:
    job_data = job.dict()

    job_data["site"] = site_value
    job_data["company"] = job_data["company_name"]

    job_data["job_type"] = (
        ", ".join(jt.value[0] for jt in job_data["job_type"])
        if job_data["job_type"]
        else None
    )
    job_data["emails"] = ", ".join(job_data["emails"]) if job_data["emails"] else None

    if job_data["location"]:
        job_data["location"] = Location(**job_data["location"]).display_location()

    _apply_compensation_fields(job_data, country, enforce_annual)

    # Champs spécifiques Naukri
    job_data["skills"] = ", ".join(job_data["skills"]) if job_data["skills"] else None
    job_data["experience_range"] = job_data.get("experience_range")
    job_data["company_rating"] = job_data.get("company_rating")
    job_data["company_reviews_count"] = job_data.get("company_reviews_count")
    job_data["vacancy_count"] = job_data.get("vacancy_count")
    job_data["work_from_home_type"] = job_data.get("work_from_home_type")

    return pd.DataFrame([job_data])


def _assemble_final_dataframe(row_frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not row_frames:
        return pd.DataFrame()

    non_empty_frames = [frame.dropna(axis=1, how="all") for frame in row_frames]
    combined = pd.concat(non_empty_frames, ignore_index=True)

    for column in desired_order:
        if column not in combined.columns:
            combined[column] = None

    combined = combined[desired_order]
    combined = combined.where(pd.notnull(combined), None)

    return combined.sort_values(
        by=["site", "date_posted"], ascending=[True, False]
    ).reset_index(drop=True)


def scrape_jobs(
    site_name: str | list[str] | Site | list[Site] | None = None,
    search_term: str | None = None,
    google_search_term: str | None = None,
    location: str | None = None,
    distance: int | None = 50,
    is_remote: bool = False,
    job_type: str | None = None,
    easy_apply: bool | None = None,
    results_wanted: int = 15,
    country_indeed: str = "usa",
    proxies: list[str] | str | None = None,
    ca_cert: str | None = None,
    description_format: str = "markdown",
    linkedin_fetch_description: bool | None = False,
    linkedin_company_ids: list[int] | None = None,
    offset: int | None = 0,
    hours_old: int = None,
    enforce_annual_salary: bool = False,
    verbose: int = 0,
    user_agent: str = None,
    **kwargs,
) -> pd.DataFrame:
    set_logger_level(verbose)

    country_enum = Country.from_string(country_indeed)
    site_targets = _resolve_site_targets(site_name)
    resolved_job_type = get_enum_from_value(job_type) if job_type else None

    scraper_input = ScraperInput(
        site_type=site_targets,
        country=country_enum,
        search_term=search_term,
        google_search_term=google_search_term,
        location=location,
        distance=distance,
        is_remote=is_remote,
        job_type=resolved_job_type,
        easy_apply=easy_apply,
        description_format=description_format,
        linkedin_fetch_description=linkedin_fetch_description,
        results_wanted=results_wanted,
        linkedin_company_ids=linkedin_company_ids,
        offset=offset,
        hours_old=hours_old,
    )

    results_by_site: dict[str, JobResponse] = {}

    with ThreadPoolExecutor() as pool:
        pending = {
            pool.submit(
                _run_single_platform, site, scraper_input, proxies, ca_cert, user_agent
            ): site
            for site in scraper_input.site_type
        }
        for future in as_completed(pending):
            site_value, response = future.result()
            results_by_site[site_value] = response

    row_frames: list[pd.DataFrame] = []
    for site_value, job_response in results_by_site.items():
        for job in job_response.jobs:
            row_frames.append(
                _flatten_job_to_row(job, site_value, country_enum, enforce_annual_salary)
            )

    return _assemble_final_dataframe(row_frames)


__all__ = [
    "scrape_jobs",
    "BDJobs",
]