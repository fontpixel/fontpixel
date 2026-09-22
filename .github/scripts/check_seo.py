"""Validate SEO metadata, social images, and crawl discovery in a complete build."""
import argparse
from collections import defaultdict
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET


class Head(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta = defaultdict(list)
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.meta[attrs.get("property", attrs.get("name", ""))].append(attrs.get("content", ""))
        elif tag == "link":
            self.links.append(attrs)


def check(root: Path):
    errors = []
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_index = ET.parse(root / "sitemap-index.xml")
    sitemap_urls = [el.text for el in sitemap_index.findall(".//s:loc", ns)]
    origin = urlparse(sitemap_urls[0])
    base = origin.path.rsplit("/", 1)[0]

    def local(url):
        parsed = urlparse(url)
        assert parsed.scheme in ("http", "https") and parsed.netloc == origin.netloc, url
        path = unquote(parsed.path)
        assert path.startswith(base + "/"), url
        return root / path[len(base):].lstrip("/")

    def page_file(url):
        p = local(url)
        return p / "index.html" if p.is_dir() else p

    def require(condition, message):
        if not condition:
            errors.append(message)

    listed = []
    for url in sitemap_urls:
        xml = ET.parse(local(url))
        listed.extend(el.text for el in xml.findall(".//s:loc", ns))
        for link in xml.findall(".//{http://www.w3.org/1999/xhtml}link"):
            require(page_file(link.attrib['href']).is_file(), f"Missing sitemap alternate: {link.attrib['href']}")
    require(len(listed) == len(set(listed)), "Duplicate sitemap URLs")
    for url in listed:
        require(page_file(url).is_file(), f"Sitemap target missing: {url}")

    required = ["description", "robots", "og:title", "og:type", "og:url", "og:site_name",
                "og:locale", "og:description", "og:image", "og:image:type", "og:image:width",
                "og:image:height", "og:image:alt", "twitter:card", "twitter:title",
                "twitter:description", "twitter:image", "twitter:image:alt"]
    canonicals = set()
    images = set()
    pages = 0
    for p in root.rglob("*.html"):
        html = p.read_text()
        head_text = html.split("</head>", 1)[0]
        # Astro's legacy URL redirect stubs intentionally have no page content.
        if 'http-equiv="refresh"' in head_text and '<main' not in html:
            continue
        pages += 1
        h = Head(head_text)
        prefix = str(p.relative_to(root))
        for field in required:
            require(len(h.meta[field]) == 1 and bool(h.meta[field][0].strip()), f"{prefix}: missing/duplicate {field}")
        require(bool(re.search(r'<html[^>]+lang="[^"]+"', html)), f"{prefix}: missing HTML language")
        require(bool(re.search(r'<title>[^<]+</title>', head_text)), f"{prefix}: missing title")
        require(bool(re.search(r'<h1\b', html)), f"{prefix}: missing h1")
        urls = [link['href'] for link in h.links if link.get('rel') == 'canonical']
        require(len(urls) == 1, f"{prefix}: missing/duplicate canonical")
        if not urls:
            continue
        canonical = urls[0]
        require(h.meta['og:url'] == [canonical], f"{prefix}: OG URL differs from canonical")
        noindex = any('noindex' in value for value in h.meta['robots'])
        if noindex:
            require(canonical not in listed, f"{prefix}: noindex URL in sitemap")
        else:
            require(canonical not in canonicals, f"{prefix}: duplicate canonical")
            canonicals.add(canonical)
            require(page_file(canonical) == p, f"{prefix}: incorrect canonical path")
            ld = re.search(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', head_text, re.S)
            require(ld is not None, f"{prefix}: missing JSON-LD")
            if ld:
                require(json.loads(ld[1]).get('url') == canonical, f"{prefix}: incorrect JSON-LD URL")
        for locale in h.meta['og:locale'] + h.meta['og:locale:alternate']:
            require(bool(re.fullmatch(r'[a-z]{2}_[A-Z]{2}', locale)), f"{prefix}: invalid OG locale {locale}")
        for link in h.links:
            if link.get('rel') == 'alternate':
                require(page_file(link['href']).is_file(), f"{prefix}: missing alternate {link['href']}")
        for url in h.meta['og:image']:
            images.add(url)
            require(h.meta['twitter:image'] == [url], f"{prefix}: Twitter image mismatch")
            require(h.meta['og:image:width'] == ['1200'] and h.meta['og:image:height'] == ['630'], f"{prefix}: image dimensions")
    require(set(listed) == canonicals, f"Sitemap mismatch: {len(canonicals - set(listed))} missing; {len(set(listed) - canonicals)} unwanted")
    for url in images:
        p = local(url)
        require(p.is_file(), f"Missing social image: {url}")
        if p.is_file():
            data = p.read_bytes()[:24]
            require(data[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', data[16:24]) == (1200, 630), f"Wrong social image dimensions: {url}")
    robots = (root / 'robots.txt').read_text()
    require(f"Sitemap: {origin.scheme}://{origin.netloc}{base}/sitemap-index.xml" in robots, "robots.txt sitemap origin mismatch")
    llms = (root / 'llms.txt').read_text()
    require(llms.startswith('# FontPixel\n'), "Missing llms.txt title")
    for url in re.findall(r'\]\((https?://[^)]+)\)', llms):
        if urlparse(url).netloc == origin.netloc:
            require(page_file(url).is_file(), f"Broken llms.txt link: {url}")
    if errors:
        raise ValueError('\n'.join(errors[:60]) + f'\n{len(errors)} SEO failures')
    return {'pages': pages, 'sitemap_urls': len(listed), 'social_images': len(images), 'errors': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    print(json.dumps(check(parser.parse_args().directory), indent=2))
