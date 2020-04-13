#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for Prismic library"""

from __future__ import (absolute_import, division, print_function, unicode_literals)

import pytest
from pytest import fixture

from prismic.cache import ShelveCache, NoCache
from prismic.exceptions import InvalidTokenError, AuthorizationNeededError, \
    UnexpectedError
from .test_prismic_fixtures import fixture_api, fixture_search, fixture_groups, \
    fixture_structured_lists, fixture_empty_paragraph, fixture_store_geopoint, \
    fixture_image_links, fixture_spans_labels, fixture_block_labels, fixture_custom_html
import json
import logging
import datetime
import prismic
from prismic import predicates
import unittest

# logging.basicConfig(level=logging.DEBUG)
# log = logging.getLogger(__name__)


@fixture()
def api_url():
    return "http://micro.prismic.io/api/v1"


@pytest.mark.asyncio
async def test_api(api_url):
    async with prismic.get(api_url) as api:
        assert api is not None


@pytest.mark.asyncio
async def test_form(api_url):
    async with prismic.get(api_url) as api:
        query = api.form("everything").ref(api.get_master()).query(predicates.at("document.type", "all"))
        response = await query.submit()

    assert response.results_size >= 2


@pytest.mark.asyncio
async def test_api_private(api_url):
    with pytest.raises(InvalidTokenError):
        # This will fail because the token is invalid, but this is how to access a private API
        async with prismic.get(api_url, 'MC5-XXXXXXX-vRfvv70'):
            pass


@pytest.mark.asyncio
async def test_references(api_url):
    preview_token = 'MC5VcXBHWHdFQUFONDZrbWp4.77-9cDx6C3lgJu-_vXZafO-_vXPvv73vv73vv70777-9Ju-_ve-_vSLvv73vv73vv73vv70O77-977-9Me-_vQ'
    async with prismic.get(api_url, preview_token) as api:
        release_ref = api.get_ref('myrelease')
        response = await api.query(predicates.at("document.type", "all"), ref=release_ref)

    assert response.results_size >= 1


@pytest.mark.asyncio
async def test_orderings(api_url):
    async with prismic.get(api_url) as api:
        response = await api.query(predicates.at("document.type", "all"), page_size=2, orderings='[my.all.number desc]')

    # The documents are now ordered using the 'number' field, highest first
    docs = response.documents
    assert docs[0].get_number('all.number').value >= docs[1].get_number('all.number').value


@pytest.mark.asyncio
async def test_as_html(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    def link_resolver(document_link):
        return "/document/%s/%s" % (document_link.id, document_link.slug)

    html = doc.as_html(link_resolver)
    assert html is not None


@pytest.mark.asyncio
async def test_html_serializer(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    def link_resolver(document_link):
        return "/document/%s/%s" % (document_link.id, document_link.slug)

    def html_serializer(element, content):
        if isinstance(element, prismic.fragments.Block.Image):
            # Don't wrap images in a <p> tag
            return element.get_view().as_html(link_resolver)
        if isinstance(element, prismic.fragments.Span.Hyperlink):
            # Add a class to links
            return """<a class="some-link" href="%s">""" % element.get_url(link_resolver) + content + "</a>"
        return None

    html = doc.get_structured_text("all.stext").as_html(link_resolver, html_serializer)
    assert html is not None


@pytest.mark.asyncio
async def test_get_text(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    author = doc.get_text("all.text")
    assert author == "all"


@pytest.mark.asyncio
async def test_get_number(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    price = doc.get_number("all.number").value
    assert price == 20.0


@pytest.mark.asyncio
async def test_get_range(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    price = doc.get_range("all.range").value
    assert price == '38'


@pytest.mark.asyncio
async def test_images(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    url = doc.get_image('all.image').url
    assert url == 'https://images.prismic.io/micro/e185bb021862c2c03a96bea92e170830908c39a3_thermometer.png?auto=compress,format'


@pytest.mark.asyncio
async def test_date(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    date = doc.get_date("all.date")
    assert date.as_datetime == datetime.datetime(2017, 1, 16, 0, 0)


@pytest.mark.asyncio
async def test_date_html(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    date = doc.get_date("all.date")
    assert date.as_html == '<time>2017-01-16</time>'


@pytest.mark.asyncio
async def test_timestamp(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    timestamp = doc.get_timestamp("all.timestamp")
    assert timestamp.as_datetime == datetime.datetime(2017, 1, 16, 7, 25, 35)


@pytest.mark.asyncio
async def test_timestamp_html(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_by_uid('all', 'all')

    timestamp = doc.get_timestamp("all.timestamp")
    assert timestamp.as_html == '<time>2017-01-16T07:25:35+0000</time>'


def test_group():
    data = "{\"id\":\"abcd\",\"type\":\"article\",\"href\":\"\",\"slugs\":[],\"tags\":[],\"data\":{\"article\":{\"documents\":{\"type\":\"Group\",\"value\":[{\"linktodoc\":{\"type\":\"Link.document\",\"value\":{\"document\":{\"id\":\"UrDejAEAAFwMyrW9\",\"type\":\"doc\",\"tags\":[],\"slug\":\"installing-meta-micro\"},\"isBroken\":false}},\"desc\":{\"type\":\"StructuredText\",\"value\":[{\"type\":\"paragraph\",\"text\":\"A detailed step by step point of view on how installing happens.\",\"spans\":[]}]}},{\"linktodoc\":{\"type\":\"Link.document\",\"value\":{\"document\":{\"id\":\"UrDmKgEAALwMyrXA\",\"type\":\"doc\",\"tags\":[],\"slug\":\"using-meta-micro\"},\"isBroken\":false}}}]}}}}"
    document = prismic.Document(json.loads(data))

    def resolver(document_link):
        return "/document/%s/%s" % (document_link.id, document_link.slug)

    group = document.get_group("article.documents")
    docs = (group and group.value) or []
    for doc in docs:
        desc = doc.get_structured_text("desc")
        link = doc.get_link("linktodoc")
    assert docs[0].get_structured_text("desc").as_html(resolver) == "<p>A detailed step by step point of view on how installing happens.</p>"


def test_link():
    data = "{\"id\":\"abcd\",\"type\":\"article\",\"href\":\"\",\"slugs\":[],\"tags\":[],\"data\":{\"article\":{\"source\":{\"type\":\"Link.document\",\"value\":{\"document\":{\"id\":\"UlfoxUnM0wkXYXbE\",\"type\":\"product\",\"tags\":[\"Macaron\"],\"slug\":\"dark-chocolate-macaron\"},\"isBroken\":false}}}}}"
    document = prismic.Document(json.loads(data))

    def resolver(document_link):
        return "/document/%s/%s" % (document_link.id, document_link.slug)

    source = document.get_link("article.source")
    url = source and source.get_url(resolver)
    assert url == "/document/UlfoxUnM0wkXYXbE/dark-chocolate-macaron"


def test_embed():
    data = "{\"id\":\"abcd\",\"type\":\"article\",\"href\":\"\",\"slugs\":[],\"tags\":[],\"data\":{\"article\":{\"video\":{\"type\":\"Embed\",\"value\":{\"oembed\":{\"provider_url\":\"http://www.youtube.com/\",\"type\":\"video\",\"thumbnail_height\":360,\"height\":270,\"thumbnail_url\":\"http://i1.ytimg.com/vi/baGfM6dBzs8/hqdefault.jpg\",\"width\":480,\"provider_name\":\"YouTube\",\"html\":\"<iframe width=\\\"480\\\" height=\\\"270\\\" src=\\\"http://www.youtube.com/embed/baGfM6dBzs8?feature=oembed\\\" frameborder=\\\"0\\\" allowfullscreen></iframe>\",\"author_name\":\"Siobhan Wilson\",\"version\":\"1.0\",\"author_url\":\"http://www.youtube.com/user/siobhanwilsonsongs\",\"thumbnail_width\":480,\"title\":\"Siobhan Wilson - All Dressed Up\",\"embed_url\":\"https://www.youtube.com/watch?v=baGfM6dBzs8\"}}}}}}"
    document = prismic.Document(json.loads(data))
    video = document.get_embed("article.video")
    # Html is the code to include to embed the object, and depends on the embedded service
    html = video and video.as_html
    assert html == "<div data-oembed=\"https://www.youtube.com/watch?v=baGfM6dBzs8\" data-oembed-type=\"video\" data-oembed-provider=\"YouTube\"><iframe width=\"480\" height=\"270\" src=\"http://www.youtube.com/embed/baGfM6dBzs8?feature=oembed\" frameborder=\"0\" allowfullscreen></iframe></div>"


def test_color():
    data = "{\"id\":\"abcd\",\"type\":\"article\",\"href\":\"\",\"slugs\":[],\"tags\":[],\"data\":{\"article\":{\"background\":{\"type\":\"Color\",\"value\":\"#000000\"}}}}"
    document = prismic.Document(json.loads(data))
    bgcolor = document.get_color("article.background")
    hex = bgcolor.value
    assert hex == "#000000"


def test_geopoint():
    data = "{\"id\":\"abcd\",\"type\":\"article\",\"href\":\"\",\"slugs\":[],\"tags\":[],\"data\":{\"article\":{\"location\":{\"type\":\"GeoPoint\",\"value\":{\"latitude\":48.877108,\"longitude\":2.333879}}}}}"
    document = prismic.Document(json.loads(data))
    # "near" predicate for GeoPoint fragments
    near = predicates.near("my.store.location", 48.8768767, 2.3338802, 10)

    # Accessing GeoPoint fragments
    place = document.get_geopoint("article.location")
    coordinates = place and ("%.6f,%.6f" % (place.latitude, place.longitude))
    assert coordinates == "48.877108,2.333879"


def test_cache(api_url):
    # Just implement your own cache object by duck-typing
    # https://github.com/prismicio/python-kit/blob/master/prismic/cache.py
    no_cache = NoCache()
    # This api will use the custom cache object
    api = prismic.get(api_url, cache=no_cache)
    assert api is not None


