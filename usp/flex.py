import logging
import requests
import sys

from requests.adapters import HTTPAdapter as RequestsHttpAdapter

from usp.fetch_parse import IndexRobotsTxtSitemapParser
from usp.log import create_logger
from usp.web_client.abstract_client import AbstractWebClient

logger = create_logger(__name__)
print = logger.info


class FlexingSocketModule:
    def __init__(self, socket_module):
        self._socket_module = socket_module


class FlexingSocketConnectionFactory:
    def __init__(self, new_conn):
        self._new_conn = new_conn

    def __call__(self, *args, **kwargs):
        conn = self._new_conn.__self__
        conn_module = sys.modules[conn.__class__.__module__]
        util_conn_module = conn_module.connection
        socket_module = util_conn_module.socket
        util_conn_module.socket = FlexingSocketModule(socket_module)
        try:
            return self._new_conn(*args, **kwargs)
        finally:
            util_conn_module.socket = socket_module


class FlexingHTTPConnectionFactory:
    def __init__(self, connection_class):
        self._connection_class = connection_class

    def __call__(self, *args, **kwargs):
        conn = self._connection_class(*args, **kwargs)
        conncls = conn.__class__
        clsname = f"{conncls.__module__}.{conncls.__qualname__}"
        print(f"{clsname}.__init__({conn.host!r}, {conn.port}, ...)")
        conn._new_conn = FlexingSocketConnectionFactory(conn._new_conn)
        return conn


class FlexingHTTPAdapter(RequestsHttpAdapter):
    def get_connection(self, url, *args, **kwargs):
        print(f"adapter.get_connection: {url!r}")
        pool = super().get_connection(url, *args, **kwargs)
        conn_class = pool.ConnectionCls
        pool.ConnectionCls = FlexingHTTPConnectionFactory(conn_class)
        return pool


class FlexingWebClient(AbstractWebClient):
    def __init__(self):
        self._session = requests.Session()
        self._max_response_data_length = None
        for prefix in list(self._session.adapters.keys()):
            self._session.mount(prefix, FlexingHTTPAdapter())

    def set_max_response_data_length(self, max_response_data_length):
        self._max_response_data_length = max_response_data_length

    def get(self, url):
        print(f"web_client.get: {url!r}")
        response = self._session.get(url)
        raise NotImplementedError


def flex_with(test_url):
    """Flex Ultimate Sitemap Parser's robots.txt parser.
    """
    print(f"test_url: {test_url!r}")
    web_client = FlexingWebClient()
    parser = IndexRobotsTxtSitemapParser(
        url="http://example.com/robots.txt",
        content=f"sitemap:{test_url}",
        recursion_level=0,
        web_client=web_client)
    parser.sitemap()
    raise NotImplementedError


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s: [%(name)s] %(message)s")
    flex_with("http://customer.com#@evil.com")


if __name__ == "__main__":
    main()
