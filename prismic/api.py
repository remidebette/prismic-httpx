# -*- coding: utf-8 -*-

"""
prismic.api
~~~~~~~~~~~

This module implements the Prismic API.

"""

from __future__ import (absolute_import, division, print_function, unicode_literals)

import sys
from contextlib import asynccontextmanager
from copy import copy, deepcopy

import httpx
from aiocache import Cache

from .connection import get_json, urlparse
from .experiments import Experiments
from . import predicates
from .exceptions import RefMissing
from .fragments import Fragment

from .utils import string_types
import logging

log = logging.getLogger(__name__)


@asynccontextmanager
async def get(url, access_token=None, cache=None, **client_kwargs):
    """Fetches the prismic api JSON. Generates only one httpx client for the async context.
    Yields :class:`~Api` object.

    Usage:
    >>> import prismic
    >>> async with prismic.get("http://your-repo.prismic.io/api", "access_token") as api:
    ...     doc = await api.get_by_uid("speculoos-macaron")

    :param url: URL to the api of the repository (mandatory).
    :param access_token: The access token (optional).
    :param cache: The cache object. Optional, will default to a in-memory cache if None is passed.
    """
    if cache is None:
        cache = Cache(Cache.MEMORY)

    async with httpx.AsyncClient(**client_kwargs) as client:
        yield Api(
            await get_json(url, access_token=access_token, cache=cache, ttl=5, client=client),
            access_token,
            cache,
            client
        )


async def get_with_client(url, access_token=None, cache=None, client=None):
    """Fetches the prismic api JSON.
    Returns :class:`~Api` object.

    :param url: URL to the api of the repository (mandatory).
    :param access_token: The access token (optional).
    :param cache: The cache object. Optional, will default to a in-memory cache if None is passed.
    :param client: The httpx client. If not passed, one client will be created for each subsequent http request.
    """
    if cache is None:
        cache = Cache(Cache.MEMORY)

    return Api(
        await get_json(url, access_token=access_token, cache=cache, ttl=5, client=client),
        access_token,
        cache,
        client
    )


class Api(object):
    """
    A Prismic API, pointing to a specific repository. Use prismic.api.get() to fetch one.

    :ivar dict bookmarks: all bookmarks, as a dict from name to document id
    :ivar array<str> types: all available types
    :ivar array<str> tags: all available tags
    :ivar Experiments experiments: information about current experiments
    :ivar str access_token: current access token (may be None)
    """

    def __init__(self, data, access_token, cache, client):
        self.cache = cache
        self.client = client
        self.refs = [Ref(ref) for ref in data.get("refs")]
        self.bookmarks = data.get("bookmarks")
        self.types = data.get("types")
        self.tags = data.get("tags")
        self.forms = data.get("forms")
        for name in self.forms:
            fields = self.forms[name].get("fields")
            for field in fields:
                if field == "q":
                    fields[field].update({"multiple": True})
        self.experiments = Experiments.parse(data.get("experiments"))
        self.oauth_initiate = data.get("oauth_initiate")
        self.oauth_token = data.get("oauth_token")
        self.access_token = access_token

        self.master = ([ref for ref in self.refs if ref.is_master_ref][:1] or [None])[0]
        if not self.master:
            log.error("No master reference found")

    async def preview_session(self, token, link_resolver, default_url):
        """Return the URL to display a given preview

        :param token: as received from Prismic server to identify the content to preview
        :param link_resolver: the link resolver to build URL for your site
        :param default_url: the URL to default to return if the preview doesn't correspond to a document
        (usually the home page of your site)

        :return: the URL to redirect the user to
        """
        resp = await get_json(token, client=self.client)
        main_document_id = resp.get("mainDocument")
        if main_document_id is None:
            return default_url
        doc = await self.get_by_id(main_document_id, ref=token)
        if doc is None == 0:
            return default_url
        return link_resolver(doc.as_link())

    def get_ref(self, label):
        """Get the :class:`~Ref` with a specific label.
        Returns :class:`~Ref` object.

        :param label: Name of the label.
        """
        ref = [ref for ref in self.refs if ref.label == label]
        return ref[0] if ref else None

    def get_master(self):
        """Returns current master :class:`~Ref` object."""
        return self.master

    def form(self, name):
        """Constructs the form with data from Api.
        Returns :class:`~SearchForm` object.

        :param name: Name of the form.
        """
        form = self.forms.get(name)
        if form is None:
            raise Exception("Bad form name %s, valid form names are: %s" % (name, ', '.join(self.forms)))
        return SearchForm(self.forms.get(name), self.access_token, self.cache, self.client)

    async def query(self, q, ref=None, page_size=None, page=None, orderings=None, after=None, fetch_links=None):
        if ref is None:
            ref = self.get_master()
        form = self.form('everything').ref(ref)
        if page_size is not None:
            form.page_size(page_size)
        if page is not None:
            form.page(page)
        if orderings is not None:
            form.orderings(orderings)
        if after is not None:
            form.after(after)
        if fetch_links is not None:
            form.fetch_links(fetch_links)
        return await form.query(q).submit()

    async def query_first(self, q, ref=None):
        resp = await self.query(q, ref, page_size=1, page=1)
        documents = resp.documents
        if len(documents) > 0:
            return documents[0]

    async def get_by_uid(self, type, uid, ref=None):
        return await self.query_first(predicates.at('my.' + type + '.uid', uid), ref)

    async def get_by_id(self, id, ref=None):
        return await self.query_first(predicates.at('document.id', id), ref)

    async def get_by_ids(self, ids, ref=None, page_size=None, page=None, orderings=None, after=None, fetch_links=None):
        return await self.query(
            predicates.in_('document.id', ids),
            ref,
            page_size=page_size,
            page=page,
            orderings=orderings,
            after=after,
            fetch_links=fetch_links
        )

    async def get_single(self, type, ref=None):
        return await self.query_first(predicates.at('document.type', type), ref)


class Ref(object):
    """
    A Prismic.io Reference (corresponds to a release)
    """

    def __init__(self, data):
        self.id = data.get("id")
        self.ref = data.get("ref")
        self.label = data.get("label")
        self.is_master_ref = data.get("isMasterRef")
        self.scheduled_at = data.get("scheduledAt")


class SearchForm(object):
    """Form to search for documents. Most of the methods return self object to allow chaining.
    """

    def __init__(self, form, access_token, cache, client):
        self.action = form.get("action")
        self.method = form.get("method")
        self.enctype = form.get("enctype")
        self.fields = form.get("fields") or {}
        self.data = {}
        # default values
        for field, value in list(self.fields.items()):
            if value.get("default"):
                self.set(field, value["default"])
        self.access_token = access_token
        self.cache = cache
        self.client = client

    def ref(self, ref):
        """:param ref: A :class:`~Ref` object or an string."""

        if isinstance(ref, Ref):
            ref = ref.ref

        return self.set('ref', ref)

    @staticmethod
    def _serialize(field):
        if isinstance(field, string_types):
            if field.startswith('my.') or field.startswith('document.') or field == 'document':
                return field
            else:
                return '"' + field + '"'
        elif hasattr(field, '__iter__'):
            strings = []
            for item in field:
                strings.append(SearchForm._serialize(item))
            return "[" + ", ".join(strings) + "]"
        else:
            return str(field)

    def query(self, *argv):
        """:param argv: Either a string query, or any number of Array corresponding to predicates.

        See the :mod:`~prismic.predicates` module for helper functions.
        """
        if len(argv) == 0:
            return self
        if isinstance(argv[0], string_types):
            q = argv[0]
        else:
            q = "["
            for predicate in argv:
                op = predicate[0]
                args = []
                for arg in predicate[1:]:
                    args.append(SearchForm._serialize(arg))
                q += "[:d = %(op)s(%(args)s)]" % {
                    'op': op,
                    'args': ", ".join(args)
                }
            q += "]"
        return self.set('q', q)

    def set(self, field, value):
        form_field = self.fields.get(field)
        if form_field and form_field.get("multiple"):
            if not self.data.get(field):
                self.data.update({field: []})
            self.data[field].append(value)
        else:
            self.data.update({field: value})
        return self

    def orderings(self, orderings):
        """Sets the query orderings

        :param orderings: String with the orderings predicate
        :returns: the SearchForm instance to chain calls
        """
        return self.set("orderings", orderings)

    def submit_assert_preconditions(self):
        if self.data.get('ref') is None:
            raise RefMissing()

    async def submit(self):
        """
        Submit the query to the Prismic.io server

        :return: :class:`~prismic.api.Response`
        """
        self.submit_assert_preconditions()
        return Response(await get_json(
            self.action,
            self.data,
            self.access_token,
            self.cache,
            client=self.client
        ))

    def page(self, page_number):
        """Set query page number

        :param page_number: int representing the page number
        """
        return self.set("page", page_number)

    def page_size(self, nb_results):
        """Set query page size

        :param nb_results: int representing the number of results per page
        """
        return self.set("pageSize", nb_results)

    def after(self, doc_id):
        """Start the result set after the given id

        :param doc_id: id of the reference document
        """
        return self.set("after", doc_id)

    def fetch(self, fields):
        """ Restrict the results document to the specified fields

        :param fields: The list of fields, array or comma separated string
        """
        if isinstance(fields, list):
            fields = ",".join(fields)
        return self.set("fetch", fields)

    def fetch_links(self, fields):
        """ Include the requested fields in the DocumentLink instances in the result

        :param fields: The list of fields, array or comma separated string
        """
        if isinstance(fields, list):
            fields = ",".join(fields)
        return self.set("fetchLinks", fields)

    def pageSize(self, nb_results):
        """Deprecated: use page_size instead
        """
        return self.page_size(nb_results)

    async def count(self):
        """Count the total number of results
        """
        resp = await copy(self).pageSize(1).submit()
        return resp.total_results_size

    def __copy__(self):
        cp = type(self)({}, self.access_token, self.cache, self.client)
        cp.action = deepcopy(self.action)
        cp.method = deepcopy(self.method)
        cp.enctype = deepcopy(self.enctype)
        cp.fields = deepcopy(self.fields)
        cp.data = deepcopy(self.data)
        return cp


class Response(object):
    """
    Prismic's response to a query.

    :ivar array<prismic.api.Document> documents: the documents of the current page
    :ivar int page: the page in this result, starting by 1
    :ivar int results_per_page: max result in a page
    :ivar int total_results_size: total number of results for this query
    :ivar int total_pages: total number of pages for this query
    :ivar str next_page: URL of the next page (may be None if on the last page )
    :ivar str prev_page: URL of the previous page (may be None)
    :ivar int results_size: number of results actually returned for the current page
    """

    def __init__(self, data):
        self._data = data
        self.documents = [Document(d) for d in data.get("results")]
        self.page = data.get("page")
        self.next_page = data.get("next_page")
        self.prev_page = data.get("prev_page")
        self.results_per_page = data.get("results_per_page")
        self.total_pages = data.get("total_pages")
        self.total_results_size = data.get("total_results_size")
        self.results_size = data.get("results_size")

    def __getattr__(self, name):
        return self._data.get(name)

    def __repr__(self):
        return "Response %s" % self._data


class Document(Fragment.WithFragments):
    """
    Represents a Prismic.io Document

    :ivar str id: document id
    :ivar str uid: document uid
    :ivar str type:
    :ivar str href:
    :ivar array<str> tags:
    :ivar array<str> slugs:
    """

    def __init__(self, data):
        Fragment.WithFragments.__init__(self, {})
        self._data = data

        fragments = {}
        if "data" in data:
            fragments = data.get("data").get(self.type)
        for (fragment_name, fragment_value) in list(fragments.items()):
            f_key = "%s.%s" % (self.type, fragment_name)

            if isinstance(fragment_value, list):
                for index, fragment_value_element in enumerate(fragment_value):
                    self.fragments["%s[%s]" % (f_key, index)] = Fragment.from_json(
                        fragment_value_element)

            elif isinstance(fragment_value, dict):
                self.fragments[f_key] = Fragment.from_json(fragment_value)

        self.slugs = ["-"]
        if data.get("slugs") is not None:
            self.slugs = [Document.__unquote(slug) for slug in data.get("slugs")]

    @staticmethod
    def __unquote(s):
        if sys.version_info >= (3, 0):
            return urlparse.unquote(s)
        else:
            return urlparse.unquote(s.encode('utf8')).decode('utf8')

    def as_link(self):
        """
        Convert the current document to a DocumentLink

        :return: :class:`~prismic.api.Fragment.DocumentLink`
        """
        data = self._data.copy()
        data['slug'] = self.slug
        return Fragment.DocumentLink({
            'document': data
        })

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError
        return self._data.get(name, None)

    @property
    def slug(self):
        """
        Return the most recent slug

        :return: str slug
        """
        return self.slugs[0] if self.slugs else "-"

    def __repr__(self):
        return "Document %s" % self.fragments

