import json
from random import randint
from time import sleep, time
from warnings import warn

from requests import post


NB_REQUETE = 10

NB_PAGE = 2


def convert_arr_2_string(values, separator):
    return separator.join(values)


def get_term(element):
    if element is None:
        return ""
    return element.text.strip()


def jprint(data):
    return json.dumps(data, sort_keys=True)


def post_data(url, payload, request_count, start_time):
    response = post(url, json=payload)

    sleep(randint(8, 15))

    request_count += 1
    elapsed = time() - start_time

    if response.status_code != 200:
        warn(
            f"Request #{request_count} - HTTP {response.status_code}"
        )

    if request_count > NB_REQUETE:
        warn("Nombre maximum de requêtes atteint.")
        return None

    try:
        return response.json()
    except Exception:
        return {}