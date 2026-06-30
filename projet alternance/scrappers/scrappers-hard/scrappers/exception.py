class JobScraperException(Exception):
    default_message = "An unknown scraper error occurred."

    def __init__(self, message: str | None = None):
        super().__init__(message if message is not None else self.default_message)


class LinkedInException(JobScraperException):
    default_message = "An error occurred with LinkedIn"


class IndeedException(JobScraperException):
    default_message = "An error occurred with Indeed"


class ZipRecruiterException(JobScraperException):
    default_message = "An error occurred with ZipRecruiter"


class GlassdoorException(JobScraperException):
    default_message = "An error occurred with Glassdoor"


class GoogleJobsException(JobScraperException):
    default_message = "An error occurred with Google Jobs"


class BaytException(JobScraperException):
    default_message = "An error occurred with Bayt"


class NaukriException(JobScraperException):
    default_message = "An error occurred with Naukri"


class BDJobsException(JobScraperException):
    default_message = "An error occurred with BDJobs"