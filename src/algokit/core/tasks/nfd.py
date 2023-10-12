import logging
from enum import Enum

import httpx

logger = logging.getLogger(__name__)

NF_DOMAINS_API_URL = "https://api.nf.domains"


class NFDMatchType(Enum):
    FULL = "full"
    TINY = "tiny"
    ADDRESS = "address"


def _process_get_request(url: str) -> dict:
    response = httpx.get(url)

    try:
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Response JSON is not a dictionary")
        return data
    except httpx.HTTPStatusError as err:
        logger.debug(f"Error response: {err.response}")

        if err.response.status_code == httpx.codes.NOT_FOUND:
            raise Exception("Not found!") from err
        if err.response.status_code == httpx.codes.BAD_REQUEST:
            raise Exception(f"Invalid request: {err.response.text}") from err
        if err.response.status_code == httpx.codes.UNAUTHORIZED:
            raise Exception(f"Unauthorized to access NFD API: {err.response.text}") from err
        if err.response.status_code == httpx.codes.FORBIDDEN:
            raise Exception(f"Forbidden to access NFD API: {err.response.text}") from err
        if err.response.status_code == httpx.codes.TOO_MANY_REQUESTS:
            raise Exception(f"Too many requests to NFD API: {err.response.text}") from err

        raise Exception(
            f'NFD lookup failed with status code {err.response.status_code} and message "{err.response.text}"'
        ) from err


def nfd_lookup_by_address(address: str, view: NFDMatchType) -> dict | str:
    view_type = "thumbnail" if view.value == NFDMatchType.ADDRESS.value else view.value
    url = f"{NF_DOMAINS_API_URL}/nfd/lookup?address={address}&view={view_type}&allowUnverified=false"
    content = _process_get_request(url)
    if isinstance(content, dict):
        return content[address]["name"] if view.value == NFDMatchType.ADDRESS.value else content

    raise Exception(f"Unexpected response from NFD API: {content}")


def nfd_lookup_by_domain(domain: str, view: NFDMatchType) -> dict | str:
    view_type = "brief" if view.value == NFDMatchType.ADDRESS.value else view.value
    url = f"{NF_DOMAINS_API_URL}/nfd/{domain}?view={view_type}&poll=false"
    content = _process_get_request(url)
    if isinstance(content, dict):
        return content["owner"] if view.value == NFDMatchType.ADDRESS.value else content

    raise Exception(f"Unexpected response from NFD API: {content}")
