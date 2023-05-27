import errno
import logging
import os
import requests
import sys

from requests.adapters import HTTPAdapter as RequestsHttpAdapter

from urllib3.exceptions import NewConnectionError

from usp.fetch_parse import IndexRobotsTxtSitemapParser
from usp.log import create_logger
from usp.web_client.abstract_client import AbstractWebClient

logger = create_logger(__name__)
print = logger.info


def raise_oserror(code):
    raise OSError(code, os.strerror(code))

hook_on = False

# https://www.gnu.org/software/libc/manual/html_node/Error-Codes.html
# ECONNABORTED (Software caused connection abort)
# A network connection was aborted locally.
#                                  ^^^^^^^ (my emphasis)
# N.B. this is not a sandbox, out hook can be overridden/rejected

def audit(event, args):
    if not hook_on:
        return
    if not event.startswith("socket."):
        return
    print(f"audit: {event} with args={args}")
    if event == "socket.connect":
        print(f"audit: blocking {event} to {args[1]}")
        raise_oserror(errno.ECONNABORTED)

sys.addaudithook(audit)


class FlexingSocketConnectionFactory:
    def __init__(self, new_conn):
        self._new_conn = new_conn

    def __call__(self, *args, **kwargs):
        global hook_on
        hook_on = True
        try:
            return self._new_conn(*args, **kwargs)
        except NewConnectionError as e:
            if isinstance(e.__cause__, ConnectionAbortedError):
                print(f"audit smashed it: {e.__cause__}")
            else:
                raise
        finally:
            hook_on = False
        raise StopFlexing


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


class StopFlexing(Exception):
    pass


def flex(test_url):
    """Flex Ultimate Sitemap Parser's robots.txt parser.
    """
    print(f"test_url: {test_url!r}")
    web_client = FlexingWebClient()
    parser = IndexRobotsTxtSitemapParser(
        url="http://example.com/robots.txt",
        content=f"sitemap:{test_url}",
        recursion_level=0,
        web_client=web_client)
    try:
        parser.sitemap()
    except StopFlexing:
        pass


def main(test_urls=None):
    if test_urls is None:
        test_urls = sys.argv[1:]
    if not test_urls:
        print("usage: flex URL...", file=sys.stderr)
        return 1

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s: [%(name)s] %(message)s")

    for i, test_url in enumerate(test_urls):
        if i != 0:
            sys.stderr.write("\n")  # XXX make log go to stdout
        flex(test_url)
        print("end of flex")


if __name__ == "__main__":
    main()
