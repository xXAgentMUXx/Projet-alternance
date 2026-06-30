from scrappers.model import Compensation, CompensationInterval, JobType
from scrappers.util import get_enum_from_job_type


def get_job_type(attributes: list) -> list[JobType]:
    results: list[JobType] = []

    for item in attributes:
        label = item["label"].replace("-", "").replace(" ", "").lower()
        enum_value = get_enum_from_job_type(label)

        if enum_value is not None:
            results.append(enum_value)

    return results


def get_compensation(compensation: dict) -> Compensation | None:
    salary_data = compensation.get("baseSalary")

    if salary_data is None and compensation.get("estimated"):
        salary_data = compensation["estimated"].get("baseSalary")

    if salary_data is None:
        return None

    interval = get_compensation_interval(salary_data["unitOfWork"])

    salary_range = salary_data.get("range", {})
    minimum = salary_range.get("min")
    maximum = salary_range.get("max")

    currency = (
        compensation["estimated"]["currencyCode"]
        if compensation.get("estimated")
        else compensation["currencyCode"]
    )

    return Compensation(
        interval=interval,
        min_amount=int(minimum) if minimum is not None else None,
        max_amount=int(maximum) if maximum is not None else None,
        currency=currency,
    )


def is_job_remote(job: dict, description: str) -> bool:
    keywords = ("remote", "work from home", "wfh")

    texts = [
        description.lower(),
        job["location"]["formatted"]["long"].lower(),
    ]

    texts.extend(attribute["label"].lower() for attribute in job["attributes"])

    searchable_text = " ".join(texts)

    return any(keyword in searchable_text for keyword in keywords)


def get_compensation_interval(interval: str) -> CompensationInterval:
    mapping = {
        "DAY": CompensationInterval.DAILY,
        "YEAR": CompensationInterval.YEARLY,
        "HOUR": CompensationInterval.HOURLY,
        "WEEK": CompensationInterval.WEEKLY,
        "MONTH": CompensationInterval.MONTHLY,
    }

    key = interval.upper()

    if key not in mapping:
        raise ValueError(f"Unsupported interval: {interval}")

    return mapping[key]