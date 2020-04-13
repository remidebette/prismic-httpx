# -*- coding: utf-8 -*-

"""
prismic.connection
~~~~~~~~~~~

This module implements the Prismic Connection handlers.

"""
from httpx import InvalidURL

try:  # 2.7
    import urllib.parse as urlparse
except ImportError:  # 3.x
    import urllib as urlparse

import httpx
import json
import re
import platform
from .exceptions import (InvalidTokenError, AuthorizationNeededError,
                         HTTPError, InvalidURLError)
from .cache import NoCache
from . import __version__ as prismic_version


async def get_using_client(full_url, client=None):
    headers = {
        "Accept": "application/json",
        "User-Agent": "Prismic-httpx-python-kit/%s Python/%s" % (
            prismic_version,
            platform.python_version()
        )
    }

    if client is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(full_url, headers=headers)

    else:
        response = await client.get(full_url, headers=headers)

    return response, response.status_code, response.headers


async def get_json(url, params=None, access_token=None, cache=None, ttl=None, client=None):
    full_params = dict() if params is None else params.copy()
    if cache is None:
        # TODO: Reimplement ShelveCache using `aiofiles`
        # cache = ShelveCache(re.sub(r'/\\', '', url.split('/')[2]))
        cache = NoCache()
    if access_token is not None:
        full_params["access_token"] = access_token
    full_url = url if len(full_params) == 0 else (url + "?" + urlparse.urlencode(full_params, doseq=True))
    cached = await cache.get(full_url)
    if cached is not None:
        return cached
    try:
        result, status_code, headers = await get_using_client(full_url, client)
        if status_code == 200:
            json_result = result.json()
            expire = ttl or get_max_age(headers)
            if expire is not None:
                await cache.set(full_url, json_result, expire)
            return json_result
        elif status_code == 401:
            if len(access_token) == 0:
                raise AuthorizationNeededError()
            else:
                raise InvalidTokenError()
        else:
            raise HTTPError(status_code, str(result.text))
    except InvalidURL as e:
        raise InvalidURLError(e)


def get_max_age(headers):
    expire_header = headers.get("Cache-Control", None)
    if expire_header is not None:
        m = re.match("max-age=(\d+)", expire_header)
        if m:
            return int(m.group(1))
    return None
