import json

from django.utils.encoding import force_text

from germanium.tools import assert_true, assert_not_equal
from germanium.test_cases.client import ClientTestCase
from germanium.annotations import login
from germanium.crawler import Crawler, LinkExtractor, HtmlLinkExtractor as OriginalHtmlLinkExtractor


def flatt_list(iterable_value):
    flatten_list = []

    for val in iterable_value:
        if isinstance(val, list):
            flatten_list += val
        else:
            flatten_list.append(val)
    return flatten_list


class JSONLinkExtractor(LinkExtractor):

    def _extract_web_links(self, data):
        return flatt_list(data.values())

    def _extract_rest_links(self, data):
        links = []
        for rest_link in data.values():
            if 'GET' in rest_link['methods']:
                links += flatt_list([rest_link['url']])
        return links

    def _extract_from_dict(self, data):
        links = []
        for key, val in data.items():
            if key == '_web_links':
                links += self._extract_web_links(val)
            elif key == '_rest_links':
                links += self._extract_rest_links(val)
            elif isinstance(val, (list, tuple)):
                links += self._extract_from_list(val)
            elif isinstance(val, dict):
                links += self._extract_from_dict(val)
        return links

    def _extract_from_list(self, data):
        links = []
        for val in data:
            if isinstance(val, dict):
                links += self._extract_from_dict(val)
            elif isinstance(val, (list, tuple)):
                links += self._extract_from_list(val)
        return links

    def extract(self, content):
        data = json.loads(content)
        if isinstance(data, dict):
            links = self._extract_from_dict(data)
        elif isinstance(data, (list, tuple)):
            links = self._extract_from_list(data)
        return links


class HTMLLinkExtractor(OriginalHtmlLinkExtractor):
    link_attr_names = ('href', 'src', 'data-resource')


class TextPlainSnippetsExtractor(LinkExtractor):

    def extract(self, content):
        links = []

        try:
            data = json.loads(content)

            html_extractor = HTMLLinkExtractor()
            for html in data.get('snippets', {}).values():
                links += html_extractor.extract(html)
        except ValueError:
            # I text/plain is not snippet return empty links
            pass

        return links


class CrawlerTestCase(ClientTestCase):

    REST_BASE = None
    exclude_urls = ()

    def get_users(self):
        raise NotImplementedError

    def get_exlude_urls(self):
        return list(self.exclude_urls) + ['/logout/']

    @login(users_generator='get_users')
    def test_crawler(self):
        self.logger.info('\n---------------------------')
        self.logger.info('Test crawling with logged user %s' % self.logged_user.user)

        tested_urls = []
        failed_urls = []

        def pre_request(url, referer, headers):
            if url.startswith('/api/'):
                headers['HTTP_X_FIELDS'] = '_rest_links,_web_links'
            if self.REST_BASE:
                headers['HTTP_X_BASE'] = str(self.REST_BASE)
            return url, headers

        def post_response(url, referer, resp, exception):
            tested_urls.append(url)
            assert_true(exception is None, msg='Received exception %s, url %s' % (force_text(exception), url))
            if resp.status_code != 200:
                failed_urls.append(url)
                self.logger.warning('Response code for url %s from referer %s should be 200 but code is %s, user %s' %
                                    (url, referer, resp.status_code, self.logged_user.user))
            assert_not_equal(resp.status_code, 500, msg='Response code for url %s from referer %s is 500, user %s' %
                             (url, referer, self.logged_user.user))
        Crawler(self.c, ('/',), self.get_exlude_urls(), pre_request, post_response,
                extra_link_extractors={'application/json; charset=utf-8': JSONLinkExtractor(),
                                       'text/plain': TextPlainSnippetsExtractor(),
                                       'default': HTMLLinkExtractor()}).run()

        self.logger.info('Completed with tested %s urls (warnings %s)' % (len(tested_urls), len(failed_urls)))
        self.logger.info('---------------------------')
