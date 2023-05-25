import logging
import requests

from requests.adapters import HTTPAdapter as RequestsHttpAdapter

from usp.fetch_parse import IndexRobotsTxtSitemapParser
from usp.log import create_logger
from usp.web_client.abstract_client import AbstractWebClient
from usp.web_client.requests_client import (
    RequestsWebClientErrorResponse,
    RequestsWebClientSuccessResponse,
)

logger = create_logger(__name__)
print = logger.info


class FlexingAdapter(RequestsHttpAdapter):
    def get_connection(self, url, *args, **kwargs):
        print(f"adapter.get_connection: {url!r}")
        raise NotImplementedError


class FlexingWebClient(AbstractWebClient):
    def __init__(self):
        self._session = requests.Session()
        self._http_adapter = FlexingAdapter()
        self._max_response_data_length = None
        for prefix in list(self._session.adapters.keys()):
            self._session.mount(prefix, self._http_adapter)

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
        format="%(levelname)s: [%(name)s] %(funcName)s: %(message)s")
    flex_with("http://customer.com#@evil.com")


if __name__ == "__main__":
    main()
