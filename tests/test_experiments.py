#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Experiments Tests for Prismic library"""

from __future__ import (absolute_import, division, print_function, unicode_literals)

import json

from pytest import fixture

import prismic
import unittest
from prismic.experiments import Experiments

experiments_json = """
{
    "draft": [
        {
            "id": "xxxxxxxxxxoGelsX",
            "name": "Exp 2",
            "variations": [
                {
                    "id": "VDUBBawGAKoGelsZ",
                    "label": "Base",
                    "ref": "VDUBBawGALAGelsa"
                },
                {
                    "id": "VDUE-awGALAGemME",
                    "label": "var 1",
                    "ref": "VDUUmHIKAZQKk9uq"
                }
            ]
        }
    ],
    "running": [
        {
            "googleId": "_UQtin7EQAOH5M34RQq6Dg",
            "id": "VDUBBawGAKoGelsX",
            "name": "Exp 1",
            "variations": [
                {
                    "id": "VDUBBawGAKoGelsZ",
                    "label": "Base",
                    "ref": "VDUBBawGALAGelsa"
                },
                {
                    "id": "VDUE-awGALAGemME",
                    "label": "var 1",
                    "ref": "VDUUmHIKAZQKk9uq"
                }
            ]
        }
    ]
}"""


@fixture()
def experiments():
    return Experiments.parse(json.loads(experiments_json))


def test_parsing(experiments):
    first = experiments.current()
    assert first.id == 'VDUBBawGAKoGelsX'
    assert first.google_id == '_UQtin7EQAOH5M34RQq6Dg'
    assert first.name == 'Exp 1'


def test_cookie_parsing(experiments):
    assert experiments.ref_from_cookie('') is None, 'Empty cookie'
    assert experiments.ref_from_cookie('Ponies are awesome') is None, 'Invalid content'

    assert 'VDUBBawGALAGelsa' == experiments.ref_from_cookie('_UQtin7EQAOH5M34RQq6Dg%200'), 'Actual running variation'
    assert 'VDUUmHIKAZQKk9uq' == experiments.ref_from_cookie('_UQtin7EQAOH5M34RQq6Dg%201'), 'Actual running variation'

    assert experiments.ref_from_cookie('_UQtin7EQAOH5M34RQq6Dg%209') is None, 'Index overflow'
    assert experiments.ref_from_cookie('_UQtin7EQAOH5M34RQq6Dg%20-1') is None, 'Negative index overflow'
    assert experiments.ref_from_cookie('NotAGoodLookingId%200') is None, 'Unknown Google ID'
    assert experiments.ref_from_cookie('NotAGoodLookingId%201') is None, 'Unknown Google ID'

