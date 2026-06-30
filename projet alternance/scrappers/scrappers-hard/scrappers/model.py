from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class JobType(Enum):

    FULL_TIME = (
        "fulltime", "périodeintegral", "estágio/trainee", "cunormăîntreagă",
        "tiempocompleto", "vollzeit", "voltijds", "tempointegral", "全职",
        "plnýúvazek", "fuldtid", "دوامكامل", "kokopäivätyö", "tempsplein",
        "πλήρηςαπασχόληση", "teljesmunkaidő", "tempopieno", "heltid",
        "jornadacompleta", "pełnyetat", "정규직", "100%", "全職",
        "งานประจำ", "tamzamanlı", "повназайнятість", "toànthờigian",
    )
    PART_TIME  = ("parttime", "teilzeit", "částečnýúvazek", "deltid")
    CONTRACT   = ("contract", "contractor")
    TEMPORARY  = ("temporary",)
    INTERNSHIP = (
        "internship", "prácticas", "ojt(onthejobtraining)",
        "praktikum", "praktik",
    )
    PER_DIEM  = ("perdiem",)
    NIGHTS    = ("nights",)
    OTHER     = ("other",)
    SUMMER    = ("summer",)
    VOLUNTEER = ("volunteer",)

class Country(Enum):

    ARGENTINA          = ("argentina",           "ar",          "com.ar")
    AUSTRALIA          = ("australia",           "au",          "com.au")
    AUSTRIA            = ("austria",             "at",          "at")
    BAHRAIN            = ("bahrain",             "bh")
    BANGLADESH         = ("bangladesh",          "bd")
    BELGIUM            = ("belgium",             "be",          "fr:be")
    BRAZIL             = ("brazil",              "br",          "com.br")
    BULGARIA           = ("bulgaria",            "bg")
    CANADA             = ("canada",              "ca",          "ca")
    CHILE              = ("chile",               "cl")
    CHINA              = ("china",               "cn")
    COLOMBIA           = ("colombia",            "co")
    COSTARICA          = ("costa rica",          "cr")
    CROATIA            = ("croatia",             "hr")
    CYPRUS             = ("cyprus",              "cy")
    CZECHREPUBLIC      = ("czech republic,czechia", "cz")
    DENMARK            = ("denmark",             "dk")
    ECUADOR            = ("ecuador",             "ec")
    EGYPT              = ("egypt",               "eg")
    ESTONIA            = ("estonia",             "ee")
    FINLAND            = ("finland",             "fi")
    FRANCE             = ("france",              "fr",          "fr")
    GERMANY            = ("germany",             "de",          "de")
    GREECE             = ("greece",              "gr")
    HONGKONG           = ("hong kong",           "hk",          "com.hk")
    HUNGARY            = ("hungary",             "hu")
    INDIA              = ("india",               "in",          "co.in")
    INDONESIA          = ("indonesia",           "id")
    IRELAND            = ("ireland",             "ie",          "ie")
    ISRAEL             = ("israel",              "il")
    ITALY              = ("italy",               "it",          "it")
    JAPAN              = ("japan",               "jp")
    KUWAIT             = ("kuwait",              "kw")
    LATVIA             = ("latvia",              "lv")
    LITHUANIA          = ("lithuania",           "lt")
    LUXEMBOURG         = ("luxembourg",          "lu")
    MALAYSIA           = ("malaysia",            "malaysia:my", "com")
    MALTA              = ("malta",               "malta:mt",    "mt")
    MEXICO             = ("mexico",              "mx",          "com.mx")
    MOROCCO            = ("morocco",             "ma")
    NETHERLANDS        = ("netherlands",         "nl",          "nl")
    NEWZEALAND         = ("new zealand",         "nz",          "co.nz")
    NIGERIA            = ("nigeria",             "ng")
    NORWAY             = ("norway",              "no")
    OMAN               = ("oman",               "om")
    PAKISTAN           = ("pakistan",            "pk")
    PANAMA             = ("panama",              "pa")
    PERU               = ("peru",               "pe")
    PHILIPPINES        = ("philippines",         "ph")
    POLAND             = ("poland",              "pl")
    PORTUGAL           = ("portugal",            "pt")
    QATAR              = ("qatar",               "qa")
    ROMANIA            = ("romania",             "ro")
    SAUDIARABIA        = ("saudi arabia",        "sa")
    SINGAPORE          = ("singapore",           "sg",          "sg")
    SLOVAKIA           = ("slovakia",            "sk")
    SLOVENIA           = ("slovenia",            "sl")
    SOUTHAFRICA        = ("south africa",        "za")
    SOUTHKOREA         = ("south korea",         "kr")
    SPAIN              = ("spain",               "es",          "es")
    SWEDEN             = ("sweden",              "se")
    SWITZERLAND        = ("switzerland",         "ch",          "de:ch")
    TAIWAN             = ("taiwan",              "tw")
    THAILAND           = ("thailand",            "th")
    TURKEY             = ("türkiye,turkey",      "tr")
    UKRAINE            = ("ukraine",             "ua")
    UNITEDARABEMIRATES = ("united arab emirates","ae")
    UK                 = ("uk,united kingdom",   "uk:gb",       "co.uk")
    USA                = ("usa,us,united states","www:us",      "com")
    URUGUAY            = ("uruguay",             "uy")
    VENEZUELA          = ("venezuela",           "ve")
    VIETNAM            = ("vietnam",             "vn",          "com")

    US_CANADA = ("usa/ca",   "www")
    WORLDWIDE = ("worldwide","www")

    @property
    def indeed_domain_value(self) -> tuple[str, str]:
        raw = self.value[1]
        subdomain, sep, api_code = raw.partition(":")
        if sep:
            return subdomain, api_code.upper()
        return raw, raw.upper()

    @property
    def glassdoor_domain_value(self) -> str:
        if len(self.value) < 3:
            raise ValueError(f"Glassdoor n'est pas disponible pour {self.name}")
        raw = self.value[2]
        subdomain, sep, tld = raw.partition(":")
        if sep:
            return f"{subdomain}.glassdoor.{tld}"
        return f"www.glassdoor.{raw}"

    def glassdoor_url(self) -> str:
        return f"https://{self.glassdoor_domain_value}/"

    @classmethod
    def from_string(cls, country_str: str) -> "Country":
        needle = country_str.strip().lower()
        for member in cls:
            if needle in member.value[0].split(","):
                return member
        valid = ", ".join(m.value[0] for m in cls)
        raise ValueError(f"Pays inconnu : '{country_str}'. Valeurs acceptées : {valid}")

class Location(BaseModel):
    country: Country | str | None = None
    city:    Optional[str] = None
    state:   Optional[str] = None

    def display_location(self) -> str:
        parts: list[str] = []

        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)

        if isinstance(self.country, str):
            parts.append(self.country)
        elif isinstance(self.country, Country) and self.country not in (
            Country.US_CANADA,
            Country.WORLDWIDE,
        ):
            raw_name = self.country.value[0]
            display_name = raw_name.split(",")[0]
            parts.append(
                display_name.upper()
                if display_name in ("usa", "uk")
                else display_name.title()
            )

        return ", ".join(parts)

class CompensationInterval(Enum):
    YEARLY  = "yearly"
    MONTHLY = "monthly"
    WEEKLY  = "weekly"
    DAILY   = "daily"
    HOURLY  = "hourly"

    @classmethod
    def get_interval(cls, pay_period: str) -> str | None:
        shortcuts = {"YEAR": cls.YEARLY, "HOUR": cls.HOURLY}
        if pay_period in shortcuts:
            return shortcuts[pay_period].value
        return cls[pay_period].value if pay_period in cls.__members__ else None


class Compensation(BaseModel):
    interval:   Optional[CompensationInterval] = None
    min_amount: float | None = None
    max_amount: float | None = None
    currency:   Optional[str] = "USD"

class DescriptionFormat(Enum):
    MARKDOWN = "markdown"
    HTML     = "html"
    PLAIN    = "plain"

class JobPost(BaseModel):
    id:              str | None = None
    title:           str
    company_name:    str | None = None
    job_url:         str
    job_url_direct:  str | None = None
    location:        Optional[Location] = None
    description:     str | None = None
    company_url:     str | None = None
    company_url_direct: str | None = None
    job_type:        list[JobType] | None = None
    compensation:    Compensation | None = None
    date_posted:     date | None = None
    emails:          list[str] | None = None
    is_remote:       bool | None = None
    listing_type:    str | None = None


    job_level:        str | None = None
    job_function:     str | None = None

    company_industry: str | None = None
    company_logo:     str | None = None

    company_addresses:     str | None = None
    company_num_employees: str | None = None
    company_revenue:       str | None = None
    company_description:   str | None = None
    banner_photo_url:      str | None = None

    skills:               list[str] | None = None
    experience_range:     str | None = None
    company_rating:       float | None = None
    company_reviews_count: int | None = None
    vacancy_count:        int | None = None
    work_from_home_type:  str | None = None


class JobResponse(BaseModel):
    jobs: list[JobPost] = []

class Site(Enum):
    LINKEDIN     = "linkedin"
    INDEED       = "indeed"
    ZIP_RECRUITER = "zip_recruiter"
    GLASSDOOR    = "glassdoor"
    GOOGLE       = "google"
    BAYT         = "bayt"
    NAUKRI       = "naukri"
    BDJOBS       = "bdjobs"


class SalarySource(Enum):
    DIRECT_DATA = "direct_data"
    DESCRIPTION = "description"

class ScraperInput(BaseModel):
    site_type:    list[Site]
    search_term:  str | None = None
    google_search_term: str | None = None

    location:     str | None = None
    country:      Country | None = Country.USA
    distance:     int | None = None
    is_remote:    bool = False
    job_type:     JobType | None = None
    easy_apply:   bool | None = None
    offset:       int = 0

    linkedin_fetch_description: bool = False
    linkedin_company_ids:       list[int] | None = None
    description_format:         DescriptionFormat | None = DescriptionFormat.MARKDOWN

    request_timeout: int = 60
    results_wanted:  int = 15
    hours_old:       int | None = None

class Scraper(ABC):

    def __init__(
        self,
        site:    Site,
        proxies: list[str] | None = None,
        ca_cert: str | None = None,
        user_agent: str | None = None,
    ):
        self.site       = site
        self.proxies    = proxies
        self.ca_cert    = ca_cert
        self.user_agent = user_agent

    @abstractmethod
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        ...