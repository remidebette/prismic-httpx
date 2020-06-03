import pytest
from pytest import fixture

import prismic


@fixture()
def api_url():
    return "REPLACE WITH YOUR URL"


@pytest.mark.asyncio_cooperative
async def test_single(api_url):
    async with prismic.get(api_url) as api:
        doc = await api.get_single("faq")

    assert doc
