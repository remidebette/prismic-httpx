## Asyncio alternative of the Python client for prismic.io

[![Latest Version](https://img.shields.io/pypi/v/prismic-httpx.svg)](https://pypi.org/project/prismic-httpx/)
[![Build Status](https://api.travis-ci.org/remidebette/prismic-httpx.png)](https://travis-ci.org/remidebette/prismic-httpx)

Disclaimer: I am not affiliated with the Prismic team and do not provide professional support.

The [Async](https://docs.python.org/3/library/asyncio.html) paradigm and the async/await syntax 
(introduced in version 3.5) are Python code styles that can be used to write concurrent coroutines.
The support for this code style is still sparse in the Python community's libraries.

You may find that the existing [Prismic Python SDK](https://github.com/prismicio/python-kit), 
based on the [requests](https://requests-fr.readthedocs.io/en/latest/) library cannot be used with the async/await
syntax.
Hence its architecture is not optimal for use with natively async webservers like 
[sanic](https://sanic.readthedocs.io/en/latest/) or tornado.

The emerging standard HTTP client for the Python asyncio community is [httpx](https://www.python-httpx.org/), 
which the current package uses.

### Getting started

#### Install the kit for your project

Simply run:

```
pip install prismic-httpx
```

#### Get started with prismic.io

You can find out [how to get started with prismic.io](https://developers.prismic.io/documentation/UjBaQsuvzdIHvE4D/getting-started) on our [prismic.io developer's portal](https://developers.prismic.io/).

#### Get started using the kit

Also on our [prismic.io developer's portal](https://developers.prismic.io/), on top of our full documentation, you will:
 * get a thorough introduction of [how to use prismic.io kits](https://developers.prismic.io/documentation/UjBe8bGIJ3EKtgBZ/api-documentation#kits-and-helpers), including this one.
 * see [what else is available for Python](https://developers.prismic.io/technologies/UjBh78uvzeMJvE4o/python): starter projects, examples, ...


#### Kit's detailed documentation

You can find the documentation of the Python kit right here: http://prismic.readthedocs.org/en/latest/

Here is a basic example of use:
(You can directly run it in a IPython console or in an async Python console: `python -m asyncio`)
```python
>>> import prismic
>>> async with prismic.get("http://your-repo.prismic.io/api", "access_token") as api:
...     doc = await api.get_by_uid("speculoos-macaron")
>>> doc.data.text
u'Speculoos Macaron'
```

#### Using Memcached (or any other cache)

By default, the kit will use a basic [in-memory cache](https://github.com/argaen/aiocache).

For use of more advanced caches (Redis, memcached), see [aiocache](https://github.com/argaen/aiocache)

For caching the requests in memory:

```python
>>> from aiocache import Cache
>>> async with prismic.get("http://your-rep.prismic.io/api", "access_token", Cache(Cache.MEMORY)) as api:
...     [...]
```

Note: The official asyncio library currently provides no support of [files I/O](https://github.com/python/asyncio/wiki/ThirdParty#filesystem)
the ShelveCache object might be introduced again in the future using [aiofiles](https://github.com/Tinche/aiofiles/) if I get time.

#### Using a Custom Request Handler

By default, the kit will use an httpx client [httpx](https://www.python-httpx.org/). 
You can override the client parameters in this way:
```python
>>> import prismic
...
>>> headers = {'X-Auth': 'from-client'}
>>> params = {'client_id': 'client1'}
>>> client_kwargs = {headers:headers, params:params}
...
>>> async with prismic.get("http://your-repo.prismic.io/api", "access_token", **client_kwargs) as api:
...     doc = await api.get_by_uid("speculoos-macaron")
>>> doc.data.text
u'Speculoos Macaron'
```

You can also monkey patch the client itself with your own in such a way:

```python
>>> import prismic
>>> import httpx
>>> headers = {'X-Auth': 'from-client'}
>>> params = {'client_id': 'client1'}
>>> with httpx.AsyncClient(headers=headers, params=params) as client:
...    api = prismic.get_with_client("http://your-rep.prismic.io/api", "access_token", client=client)
...    [...]
```

### Changelog

Need to see what changed, or to upgrade your kit? We keep our changelog on [this repository's "Releases" tab](https://github.com/remidebette/prismic-httpx/releases).

### Contribute to the kit

Contribution is open to all developer levels

#### Install the kit locally

This kit gets installed like any Python library.

#### Test

Please write tests for any bugfix or new feature.

If you find existing code that is not optimally tested and wish to make it better, we really appreciate it; but you should document it on its own branch and its own pull request.

You can launch tests using: `pytest test`.

#### Documentation

Please document any bugfix or new feature.

If you find existing code that is not optimally documented and wish to make it better, we really appreciate it; but you should document it on its own branch and its own pull request.

### Licence

This software is licensed under the Apache 2 license, quoted below.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this project except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
