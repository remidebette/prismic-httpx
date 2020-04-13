#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for Prismic library"""

from __future__ import (absolute_import, division, print_function, unicode_literals)

from prismic import connection


def test_missing_header_key():
    headers = {}
    max_age = connection.get_max_age(headers)
    assert max_age is None

