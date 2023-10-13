import json
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


def nfd_lookup_by_address(address: str, view: NFDMatchType) -> str:
    """
    Perform a lookup on an API to retrieve information about a given address.

    Args:
        address (str): The address to perform the lookup on.
        view (NFDMatchType): The type of view to retrieve from the API.
        It can be one of the following: "full", "tiny", or "address".

    Returns:
        str: If the view is "address", returns the name associated with the address as a string.
        If the view is not "address", returns the JSON response from the API as a string with an indentation of 2.

    Raises:
        Exception: If the content from the API is not a dictionary, raises an exception with the unexpected response.
    """

    view_type = "thumbnail" if view.value == NFDMatchType.ADDRESS.value else view.value
    url = f"{NF_DOMAINS_API_URL}/nfd/lookup?address={address}&view={view_type}&allowUnverified=false"
    content = _process_get_request(url)
    if isinstance(content, dict):
        if view.value == NFDMatchType.ADDRESS.value:
            return str(content[address]["name"])
        else:
            return json.dumps(content, indent=2)

    raise Exception(f"Unexpected response from NFD API: {content}")


def nfd_lookup_by_domain(domain: str, view: NFDMatchType) -> str:
    """
    Performs a lookup on a given domain using the NF Domains API.

    Args:
        domain (str): The domain to be looked up.
        view (NFDMatchType): The type of information to retrieve.
        It can be one of the following: NFDMatchType.FULL, NFDMatchType.TINY, or NFDMatchType.ADDRESS.

    Returns:
        str: If the view is NFDMatchType.ADDRESS, returns the owner of the domain as a string.
        If the view is not NFDMatchType.ADDRESS, returns the response JSON stringified with indentation.

    Raises:
        Exception: If the response from the NF Domains API is not a dictionary.
    """

    view_type = "brief" if view.value == NFDMatchType.ADDRESS.value else view.value
    url = f"{NF_DOMAINS_API_URL}/nfd/{domain}?view={view_type}&poll=false"
    content = _process_get_request(url)
    if isinstance(content, dict):
        if view == NFDMatchType.ADDRESS:
            return str(content["owner"])
        else:
            return json.dumps(content, indent=2)

    raise Exception(f"Unexpected response from NFD API: {content}")
