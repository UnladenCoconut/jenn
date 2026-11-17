import urllib.parse
import urllib.request

import lxml
from lxml import etree,html
import urllib
from urllib.parse import urlparse, ParseResult
import re
import os 

from typing import Final, cast

# robots.txt -> YOAST SEO section: https://nordicmodelnow.org/sitemap_index.xml

#dated articles
POSTS_SITEMAP: Final[str] = 'https://nordicmodelnow.org/post-sitemap.xml'

#includes facts/myths about prostitution articles
PAGE_SITEMAP: Final[str] = 'https://nordicmodelnow.org/page-sitemap.xml'

TESTIMONIAL_SITEMAP: Final[str] = 'https://nordicmodelnow.org/jetpack-testimonial-sitemap.xml'

XMLNS: Final[str] = 'http://www.sitemaps.org/schemas/sitemap/0.9'

#use a user agent string in requests when fetching pages to avoid being rate limited

USER_AGENT = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

TIMEOUT = 5.0 #seconds

def sitemap_urls(url: str) -> list[ParseResult]:
    request = urllib.request.Request(url,headers=USER_AGENT)
    response = urllib.request.urlopen(request,timeout=TIMEOUT).read()

    xml: etree._Element = etree.fromstring(response)
    urls = xml.findall(f'.//{{{XMLNS}}}url/{{{XMLNS}}}loc')
    return cast(list[ParseResult],[urlparse(x.text) for x in urls])

def main():

    urls = dict() #key: name / root folder. use value.path as file name (replace / with -)

    testimonial_urls = sitemap_urls(TESTIMONIAL_SITEMAP)
    testimonial_urls = [url for url in testimonial_urls if re.match(r'^\/testimonial\/.+$',url.path)]
    urls['testimonials'] = testimonial_urls

    post_urls = sitemap_urls(POSTS_SITEMAP)
    post_urls = [url for url in post_urls if re.match(r'^\/\d{4}\/\d{2}\/\d{2}\/.*$',url.path)]
    urls['posts'] = post_urls

    page_urls = sitemap_urls(PAGE_SITEMAP)
    page_urls = [url for url in page_urls if re.match(r'^\/(myths-about-prostitution|facts-about-prostitution)\/.+$',url.path)]
    urls['pages'] = page_urls
     
    for k,v in urls.items():
        print(f'{k}: {len(v)}')

    for (k,v) in urls.items():
        os.makedirs(os.path.join('data',k),exist_ok=True)

        url: ParseResult
        for url in v:

            request = urllib.request.Request(url.geturl(),headers=USER_AGENT)
            response = urllib.request.urlopen(request,timeout=TIMEOUT).read()
            page_html: html.HtmlElement = html.fromstring(response)
            html_title: html.HtmlElement = cast(html.HtmlElement,page_html.find('./head/title'))
            html_content_elements: list[html.HtmlElement] = page_html.find_class('entry-content')

            if len(html_content_elements) > 1:
                raise RuntimeError("found multiple 'entry-content' elements on page")

            html_content: html.HtmlElement = html_content_elements[0]

            title: str = cast(str,html_title.text)

            print(f'{url.geturl()}')
            print(f'\ttitle: {title}') #todo remove '| Nordic Model Now!' postfix if present
            file_name = urllib.parse.unquote(url.path.strip('/')).replace('/','-')
            file_path = os.path.join('data',k,file_name)
            print(f'\tsave to "{file_path}"')

            for e in html_content.xpath(r"//*[@class='robots-nocontent']"):
                print('e')
            
            #TODO: remove whitespace lines, 'share this' stuff, 'further reading'
            # with open(file_path,'w') as f:
            #     f.write(title)
            #     f.write('\n\n')
            #     f.write(content)
        


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('(User quit)')