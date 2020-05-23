#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for Prismic library"""

from __future__ import (absolute_import, division, print_function, unicode_literals)

import asyncio

import pytest
from pytest import fixture

from prismic.exceptions import InvalidTokenError, AuthorizationNeededError, InvalidURLError
import json
import prismic
from prismic import predicates
from aiocache import Cache

# logging.basicConfig(level=logging.DEBUG)
# log = logging.getLogger(__name__)
from tests import test_prismic_fixtures


@fixture()
def api_url():
    return "http://micro.prismic.io/api"


@fixture()
def token():
    return "MC5VcXBHWHdFQUFONDZrbWp4.77-9cDx6C3lgJu-_vXZafO-_vXPvv73vv73vv70777-9Ju-_ve-_vSLvv73vv73vv73vv70O77-977-9Me-_vQ"


@fixture()
def fixture_api():
    return json.loads(test_prismic_fixtures.fixture_api)


@fixture()
def fixture_search():
    return json.loads(test_prismic_fixtures.fixture_search)


@fixture()
def fixture_structured_lists():
    return json.loads(test_prismic_fixtures.fixture_structured_lists)


@fixture()
def fixture_empty_paragraph():
    return json.loads(test_prismic_fixtures.fixture_empty_paragraph)


@fixture()
def fixture_block_labels():
    return json.loads(test_prismic_fixtures.fixture_block_labels)


@fixture()
def fixture_store_geopoint():
    return json.loads(test_prismic_fixtures.fixture_store_geopoint)


@fixture()
def fixture_groups():
    return json.loads(test_prismic_fixtures.fixture_groups)


@fixture()
def fixture_image_links():
    return json.loads(test_prismic_fixtures.fixture_image_links)


@fixture()
def fixture_spans_labels():
    return json.loads(test_prismic_fixtures.fixture_spans_labels)


@fixture()
def fixture_custom_html():
    return json.loads(test_prismic_fixtures.fixture_custom_html)


@fixture()
def fixture_slices():
    return json.loads(test_prismic_fixtures.fixture_slices)


@fixture()
def fixture_composite_slices():
    return json.loads(test_prismic_fixtures.fixture_composite_slices)


@fixture()
async def api(fixture_api, token):
    return prismic.Api(fixture_api, token, Cache(Cache.MEMORY), None)


@fixture()
async def integration_api(api_url, token):
    async with prismic.get(api_url, token) as api:
        yield api


def link_resolver(document_link):
    if document_link.is_broken:
        return "#broken"
    else:
        return "/document/%s/%s" % (document_link.id, document_link.slug)


def html_serializer(element, content):
    if isinstance(element, prismic.fragments.Block.Image):
        return element.get_view().as_html(link_resolver)
    if isinstance(element, prismic.fragments.Span.Hyperlink):
        return """<a class="some-link" href="%s">""" % element.get_url(link_resolver) + content + "</a>"
    return None


@pytest.mark.asyncio_cooperative
async def test_get_api(integration_api):
    assert len(integration_api.forms) >= 0


@pytest.mark.asyncio_cooperative
async def test_api_get_errors(api_url):
    with pytest.raises(InvalidTokenError):
        async with prismic.get(api_url, "wrong"):
            pass

    with pytest.raises(AuthorizationNeededError):
        async with prismic.get(api_url, ""):
            pass

    with pytest.raises(InvalidURLError):
        async with prismic.get("htt://wrong_on_purpose", ""):
            pass


@pytest.mark.asyncio_cooperative
async def test_search_form(integration_api):
    form = integration_api.form("everything")
    form.ref(integration_api.get_master())
    resp = await form.submit()
    assert len(resp.documents) >= 2


@pytest.mark.asyncio_cooperative
async def test_search_form_orderings(integration_api):
    form = integration_api.form("everything")
    form.ref(integration_api.get_master())
    form.query('[[:q = at(document.type, "all")]]')
    form.orderings("[my.all.number]")
    resp = await form.submit()
    docs = resp.documents
    assert docs[0].uid == 'all'
    assert docs[1].uid == 'all1'
    assert docs[2].uid == 'all2'


@pytest.mark.asyncio_cooperative
async def test_search_form_page_size(integration_api):
    form = integration_api.form("everything").page_size(2)
    form.ref(integration_api.get_master())
    response = await form.submit()
    assert len(response.documents) == 2
    assert response.results_per_page == 2


@pytest.mark.asyncio_cooperative
async def test_search_form_first_page(integration_api):
    form = integration_api.form("everything").pageSize(2)
    form.ref(integration_api.get_master())
    response = await form.submit()
    assert response.page == 1
    assert len(response.documents) == 2
    assert response.results_size == len(response.documents)
    assert response.prev_page is None
    assert response.next_page is not None


@pytest.mark.asyncio_cooperative
async def test_search_form_page(integration_api):
    form = integration_api.form("everything").pageSize(2).page(2)
    form.ref(integration_api.get_master())
    response = await form.submit()
    assert response.page == 2
    assert len(response.documents) == 2
    assert response.results_size == len(response.documents)
    assert response.prev_page is not None
    assert response.next_page is not None


@pytest.mark.asyncio_cooperative
async def test_search_form_count(integration_api):
    form = integration_api.form("everything")
    form.ref(integration_api.get_master())
    nb_docs = await form.count()
    assert nb_docs >= 2


@pytest.mark.asyncio_cooperative
async def test_query(integration_api):
    resp = await integration_api\
        .query(predicates.at('document.id', 'WHx-gSYAAMkyXYX_'))
    doc = resp.documents[0]
    assert doc.id == 'WHx-gSYAAMkyXYX_'


@pytest.mark.asyncio_cooperative
async def test_query_first(integration_api):
    doc = await integration_api.query_first(predicates.at('document.id', 'WHx-gSYAAMkyXYX_'))
    assert doc.id == 'WHx-gSYAAMkyXYX_'


@pytest.mark.asyncio_cooperative
async def test_query_first_no_result(integration_api):
    doc = await integration_api.query_first(predicates.at('document.id', 'NotAValidId'))
    assert doc is None


@pytest.mark.asyncio_cooperative
async def test_get_by_uid(integration_api):
    doc = await integration_api.get_by_uid('all', 'all')
    assert doc.id == 'WHx-gSYAAMkyXYX_'


@pytest.mark.asyncio_cooperative
async def test_get_by_id(integration_api):
    doc = await integration_api.get_by_id('WHx-gSYAAMkyXYX_')
    assert doc.id == 'WHx-gSYAAMkyXYX_'


@pytest.mark.asyncio_cooperative
async def test_get_by_ids(integration_api):
    result = await integration_api.get_by_ids(['WHx-gSYAAMkyXYX_', 'WHyJqyYAAHgyXbcj'])
    ids = sorted([doc.id for doc in result.documents])
    assert ids[0] == 'WHx-gSYAAMkyXYX_'
    assert ids[1] == 'WHyJqyYAAHgyXbcj'


@pytest.mark.asyncio_cooperative
async def test_get_single(integration_api):
    doc = await integration_api.get_single('single')
    assert doc.id == 'V_OplCUAACQAE0lA'


@pytest.mark.asyncio_cooperative
async def test_linked_documents(integration_api):
    resp = await integration_api\
        .form("everything")\
        .ref(integration_api.get_master())\
        .query('[[:d = at(document.id, "WHx-gSYAAMkyXYX_")]]')\
        .submit()
    doc = resp.documents[0]
    assert len(doc.linked_documents) == 2


@pytest.mark.asyncio_cooperative
async def test_fetch_links(integration_api):
    resp = await integration_api\
        .form('everything')\
        .ref(integration_api.get_master())\
        .fetch_links('all.text')\
        .query(predicates.at('document.id', 'WHx-gSYAAMkyXYX_')) \
        .submit()
    article = resp.documents[0]
    links = article.get_all('all.link_document')
    assert links[0].get_text('all.text') == 'all1'


@pytest.mark.asyncio_cooperative
async def test_fetch_links_list(integration_api):
    resp = await integration_api\
        .form('everything')\
        .ref(integration_api.get_master())\
        .fetch_links(['all.text', 'all.number'])\
        .query(predicates.at('document.id', 'WH2PaioAALYBEgug')) \
        .submit()
    article = resp.documents[0]
    links = article.get_all('all.link_document')
    assert links[0].get_text('all.text') == 'all'
    assert links[0].get_text('all.number') == 20


def test_get_ref_master(api):
    assert api.get_ref("Master").ref == "UgjWQN_mqa8HvPJY"


def test_get_ref(api):
    assert api.get_ref("San Francisco Grand opening").ref == "UgjWRd_mqbYHvPJa"


def test_get_master(api):
    assert api.get_master().ref == "UgjWQN_mqa8HvPJY"
    assert api.get_master().id == "master"


def test_document(fixture_search):
    docs = [prismic.Document(doc) for doc in fixture_search]
    assert len(docs) == 3
    doc = docs[0]
    assert doc.slug == "vanilla-macaron"


def test_empty_slug(fixture_search):
    doc_json = fixture_search[0]
    doc_json["slugs"] = None
    doc = prismic.Document(doc_json)
    assert doc.slug == "-"


def test_as_html(fixture_search):
    doc_json = fixture_search[0]
    doc = prismic.Document(doc_json)
    expected_html = (
        """<section data-field="product.image"><img src="https://wroomio.s3.amazonaws.com/micro/0417110ebf2dc34a3e8b7b28ee4e06ac82473b70.png" alt="" width="500" height="500" /></section>"""
        """<section data-field="product.short_lede"><h2>Crispiness and softness, rolled into one</h2></section>"""
        """<section data-field="product.description"><p>Experience the ultimate vanilla experience. Our vanilla Macarons are made with our very own (in-house) <strong>pure extract of Madagascar vanilla</strong>, and subtly dusted with <strong>our own vanilla sugar</strong> (which we make from real vanilla beans).</p></section>"""
        """<section data-field="product.testimonial_author[0]"><h3>Chef Guillaume Bort</h3></section>"""
        """<section data-field="product.testimonial_quote[0]"><p>The taste of pure vanilla is very hard to tame, and therefore, most cooks resort to substitutes. <strong>It takes a high-skill chef to know how to get the best of tastes, and </strong><em><strong>Les Bonnes Choses</strong></em><strong>&#x27;s vanilla macaron does just that</strong>. The result is more than a success, it simply is a gastronomic piece of art.</p></section>"""
        """<section data-field="product.related[0]"><a href="document/UdUjvt_mqVNObPeO">dark-chocolate-macaron</a></section>"""
        """<section data-field="product.related[1]"><a href="document/UdUjsN_mqT1ObPeM">salted-caramel-macaron</a></section>"""
        """<section data-field="product.price"><span class="number">3.55</span></section>"""
        """<section data-field="product.color"><span class="color">#ffeacd</span></section>"""
        """<section data-field="product.flavour[0]"><span class="text">Vanilla</span></section>"""
        """<section data-field="product.name"><h1>Vanilla Macaron</h1></section>"""
        """<section data-field="product.allergens"><span class="text">Contains almonds, eggs, milk</span></section>"""
    )
    doc_html = doc.as_html(lambda link_doc: "document/%s" % link_doc.id)
    # Comparing len rather than actual strings because json loading is not in a deterministic order for now
    assert doc_html == expected_html


def test_default_params_empty(api):
    form = api.form("everything")
    assert len(form.data) == 0


def test_query_append_value(api):
    form = api.form("everything")
    form.query("[[bar]]")
    assert len(form.data) == 1
    assert form.data["q"] == ["[[bar]]"]


def test_ref_replace_value(api):
    form = api.form("everything")
    form.ref("foo")
    assert len(form.data) == 1
    assert form.data["ref"] == "foo"
    form.ref("bar")
    assert len(form.data) == 1
    assert form.data["ref"] == "bar"


def test_set_page_size(api):
    form = api.form("everything")
    form.page_size(3)
    assert len(form.data) == 1
    assert form.data["pageSize"] == 3


def test_set_page(api):
    form = api.form("everything")
    form.page(3)
    assert len(form.data) == 1
    assert form.data["page"] == 3


@fixture()
def doc(fixture_search):
    doc_json = fixture_search[0]
    return prismic.Document(doc_json)


def test_image(doc):
    assert doc.get_image("product.image", "main").width == 500
    assert doc.get_image("product.image", "icon").width == 250
    expected_html = \
        ("""<img """
         """src="https://wroomio.s3.amazonaws.com/micro/babdc3421037f9af77720d8f5dcf1b84c912c6ba.png" """
         """alt="" width="250" height="250" />""")
    assert expected_html == doc.get_image("product.image", "icon").as_html(link_resolver)


def test_number(doc):
    assert doc.get_number("product.price").__str__() == "3.55"


def test_color(doc):
    assert doc.get_color("product.color").__str__() == "#ffeacd"


def test_text(doc):
    assert doc.get_text("product.allergens").__str__() == "Contains almonds, eggs, milk"

    text = prismic.Fragment.Text("a&b 42 > 41")
    assert text.as_html == '<span class="text">a&amp;b 42 &gt; 41</span>', "HTML escape"


def test_structured_text_heading(doc):
    html = doc.get_html("product.short_lede", lambda x: "/x")
    assert "<h2>Crispiness and softness, rolled into one</h2>" == html


def test_structured_text_paragraph():
    span_sample_data = {"type": "paragraph",
                        "text": "To be or not to be ?",
                        "spans": [
                            {"start": 3, "end": 5, "type": "strong"},
                            {"start": 16, "end": 18, "type": "strong"},
                            {"start": 3, "end": 5, "type": "em"}
                        ]}
    p = prismic.fragments.StructuredText([span_sample_data])
    p_html = p.as_html(lambda x: "/x")
    assert p_html == "<p>To <em><strong>be</strong></em> or not to <strong>be</strong> ?</p>"

    p = prismic.fragments.StructuredText([{"type": "paragraph", "text": "a&b 42 > 41", "spans": []}])
    p_html = p.as_html(lambda x: "/x")
    assert p_html == "<p>a&amp;b 42 &gt; 41</p>", "Paragraph HTML escape"

    p = prismic.fragments.StructuredText([{"type": "heading2", "text": "a&b 42 > 41", "spans": []}])
    p_html = p.as_html(lambda x: "/x")
    assert p_html == "<h2>a&amp;b 42 &gt; 41</h2>", "Header HTML escape"


def test_spans(fixture_spans_labels):
    p = prismic.fragments.StructuredText(fixture_spans_labels.get("value"))
    p_html = p.as_html(lambda x: "/x")
    assert p_html == ("""<p>Two <strong><em>spans</em> with</strong> the same start</p>"""
                              """<p>Two <em><strong>spans</strong> with</em> the same start</p>"""
                              """<p>Span till the <span class="tip">end</span></p>""")


def test_lists(fixture_structured_lists):
    doc_json = fixture_structured_lists[0]
    doc = prismic.Document(doc_json)
    doc_html = doc.get_structured_text("article.content").as_html(lambda x: "/x")
    expected = ("""<ul><li>Element1</li><li>Element2</li><li>Element3</li></ul>"""
                """<p>Ordered list:</p><ol><li>Element1</li><li>Element2</li><li>Element3</li></ol>""")
    assert doc_html == expected


def test_empty_paragraph(fixture_empty_paragraph):
    doc_json = fixture_empty_paragraph
    doc = prismic.Document(doc_json)

    doc_html = doc.get_field('announcement.content').as_html(link_resolver)
    expected = """<p>X</p><p></p><p>Y</p>"""
    assert doc_html == expected


def test_block_labels(fixture_block_labels):
    doc = prismic.Document(fixture_block_labels)

    doc_html = doc.get_field('announcement.content').as_html(link_resolver)
    expected = """<p class="code">some code</p>"""
    assert doc_html == expected


def test_get_text(fixture_search):
    doc_json = fixture_search[0]
    doc = prismic.Document(doc_json)
    assert doc.get_text('product.description') == 'Experience the ultimate vanilla experience. Our vanilla Macarons are made with our very own (in-house) pure extract of Madagascar vanilla, and subtly dusted with our own vanilla sugar (which we make from real vanilla beans).'


def test_document_link():
    test_paragraph = {
        "type": "paragraph",
        "text": "bye",
        "spans": [
            {
                "start": 0,
                "end": 3,
                "type": "hyperlink",
                "data": {
                    "type": "Link.document",
                    "value": {
                        "document": {
                            "id": "UbiYbN_mqXkBOgE2", "type": "article", "tags": ["form"], "slug": "-"
                        },
                        "isBroken": False
                    }
                }
            },
            {"start": 0, "end": 3, "type": "strong"}
        ]
    }
    p = prismic.fragments.StructuredText([test_paragraph])

    def link_resolver(document_link):
        return "/document/%s/%s" % (document_link.id, document_link.slug)

    p_html = p.as_html(link_resolver)
    assert p_html == """<p><strong><a href="/document/UbiYbN_mqXkBOgE2/-">bye</a></strong></p>"""


def test_geo_point(fixture_store_geopoint):
    store = prismic.Document(fixture_store_geopoint)
    geopoint = store.get_field("store.coordinates")
    assert geopoint.as_html == ("""<div class="geopoint"><span class="latitude">37.777431</span>"""
                      """<span class="longitude">-122.415419</span></div>""")


def test_group(fixture_groups):
    contributor = prismic.Document(fixture_groups)
    links = contributor.get_group("contributor.links")
    assert len(links.value) == 2


def test_slicezone(fixture_slices):
    maxDiff = 10000
    doc = prismic.Document(fixture_slices)
    slices = doc.get_slice_zone("article.blocks")
    slices_html = slices.as_html(link_resolver)
    expected_html = (
        """<div data-slicetype="features" class="slice"><section data-field="illustration"><img src="https://wroomdev.s3.amazonaws.com/toto/db3775edb44f9818c54baa72bbfc8d3d6394b6ef_hsf_evilsquall.jpg" alt="" width="4285" height="709" /></section>"""
        """<section data-field="title"><span class="text">c&#x27;est un bloc features</span></section></div>\n"""
        """<div data-slicetype="text" class="slice"><p>C&#x27;est un bloc content</p></div>""")
    # Comparing len rather than actual strings because json loading is not in a deterministic order for now
    assert slices_html == expected_html


def test_composite_slices(fixture_composite_slices):
    maxDiff = 1000
    doc = prismic.Document(fixture_composite_slices)
    slices = doc.get_slice_zone("test.body")
    slices_html = slices.as_html(link_resolver)
    expected_html = """<div data-slicetype="slice-a" class="slice"><section data-field="non-repeat-text"><p>Slice A non-repeat text</p></section><section data-field="non-repeat-title"><h1>Slice A non-repeat title</h1></section><section data-field="repeat-text"><p>Repeatable text A</p></section><section data-field="repeat-title"><h1>Repeatable title A</h1></section>
<section data-field="repeat-text"><p>Repeatable text B</p></section><section data-field="repeat-title"><h1>Repeatable title B</h1></section></div>
<div data-slicetype="slice-b" class="slice"><section data-field="image"><img src="https://prismic-io.s3.amazonaws.com/tails/014c1fe46e3ceaf04b7cc925b2ea7e8027dc607a_mobile_header_tp.png" alt="" width="800" height="500" /></section><section data-field="title"><h1>Slice A non-repeat title</h1></section></div>"""
    # Comparing len rather than actual strings because json loading is not in a deterministic order for now
    assert len(expected_html) == len(slices_html)


def test_image_links(fixture_image_links):
    maxDiff = 10000
    text = prismic.fragments.StructuredText(fixture_image_links.get('value'))

    assert text.as_html(link_resolver) == (
        """<p>Here is some introductory text.</p>"""
        """<p>The following image is linked.</p>"""
        """<p class="block-img"><a href="http://google.com/">"""
        """<img src="http://fpoimg.com/129x260" alt="" width="260" height="129" /></a></p>"""
        """<p><strong>More important stuff</strong></p><p>The next is linked to a valid document:</p>"""
        """<p class="block-img"><a href="/document/UxCQFFFFFFFaaYAH/something-fantastic">"""
        """<img src="http://fpoimg.com/400x400" alt="" width="400" height="400" /></a></p>"""
        """<p>The next is linked to a broken document:</p><p class="block-img"><a href="#broken">"""
        """<img src="http://fpoimg.com/250x250" alt="" width="250" height="250" /></a></p>"""
        """<p>One more image, this one is not linked:</p><p class="block-img">"""
        """<img src="http://fpoimg.com/199x300" alt="" width="300" height="199" /></p>"""
    )


def test_custom_html(fixture_custom_html):
    maxDiff = 10000
    text = prismic.fragments.StructuredText(fixture_custom_html.get('value'))

    assert text.as_html(link_resolver, html_serializer) == (
        """<p>Here is some introductory text.</p>"""
        """<p>The following image is linked.</p>"""
        """<a href="http://google.com/"><img src="http://fpoimg.com/129x260" alt="" width="260" height="129" /></a>"""
        """<p><strong>More important stuff</strong></p><p>The next is linked to a valid document:</p>"""
        """<a href="/document/UxCQFFFFFFFaaYAH/something-fantastic">"""
        """<img src="http://fpoimg.com/400x400" alt="" width="400" height="400" /></a>"""
        """<p>The next is linked to a broken document:</p><a href="#broken">"""
        """<img src="http://fpoimg.com/250x250" alt="" width="250" height="250" /></a>"""
        """<p>One more image, this one is not linked:</p>"""
        """<img src="http://fpoimg.com/199x300" alt="" width="300" height="199" />"""
        """<p>This <a class="some-link" href="/document/UlfoxUnM0wkXYXbu/les-bonnes-chosess-internship-a-testimony">"""
        """paragraph</a> contains an hyperlink.</p>"""
    )


def test_at(api):
    f = api\
        .form("everything")\
        .ref(api.get_master())\
        .query(predicates.at('document.id', 'UlfoxUnM0wkXYXbZ'))
    assert f.data['q'] == ["[[:d = at(document.id, \"UlfoxUnM0wkXYXbZ\")]]"]


def test_not(api):
    f = api\
        .form("everything")\
        .ref(api.get_master())\
        .query(predicates.not_('document.id', 'UlfoxUnM0wkXYXbZ'))
    assert f.data['q'] == ["[[:d = not(document.id, \"UlfoxUnM0wkXYXbZ\")]]"]


def test_any(api):
    f = api \
        .form("everything") \
        .ref(api.get_master()) \
        .query(predicates.any('document.type', ['article', 'form-post']))
    assert f.data['q'] == ['[[:d = any(document.type, ["article", "form-post"])]]']


def test_similar(api):
    f = api \
        .form("everything") \
        .ref(api.get_master()) \
        .query(predicates.similar('idOfSomeDocument', 10))
    assert f.data['q'] == ['[[:d = similar("idOfSomeDocument", 10)]]']


def test_multiple_predicates(api):
    f = api \
        .form("everything") \
        .ref(api.get_master()) \
        .query(
            predicates.month_after('my.form-post.publication-date', 4),
            predicates.month_before('my.form-post.publication-date', 'December')
        )
    assert f.data['q'] == ['[[:d = date.month-after(my.form-post.publication-date, 4)][:d = date.month-before(my.form-post.publication-date, "December")]]']


def test_number_lt(api):
    f = api \
        .form("everything") \
        .ref(api.get_master()) \
        .query(predicates.lt('my.form-post.publication-date', 4))
    assert f.data['q'] == ['[[:d = number.lt(my.form-post.publication-date, 4)]]']


def test_number_in_range(api):
    f = api \
        .form("everything") \
        .ref(api.get_master()) \
        .query(predicates.in_range('my.product.price', 2, 4.5))
    assert f.data['q'] == ['[[:d = number.inRange(my.product.price, 2, 4.5)]]']


def test_geopoint_near(api):
    f = api \
        .form("everything") \
        .ref(api.get_master()) \
        .query(predicates.near('my.store.coordinates', 40.689757, -74.0451453, 15))
    assert f.data['q'] == ['[[:d = geopoint.near(my.store.coordinates, 40.689757, -74.0451453, 15)]]']


@fixture()
async def cache():
    return Cache(Cache.MEMORY)


@pytest.mark.asyncio_cooperative
async def test_set_get(cache):
    await cache.set("foo", "bar", 3600)
    assert await cache.get("foo") == "bar"


@pytest.mark.asyncio_cooperative
async def test_expiration(cache):
    await cache.set("toto", "tata", 2)
    await asyncio.sleep(3)
    assert await cache.get("toto") is None

