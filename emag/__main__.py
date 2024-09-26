
from requests_cache import CachedSession
from requests import Request
import requests
import random
from dataclasses import dataclass
from bs4 import BeautifulSoup
import time
import re

agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
session = CachedSession(backend='filesystem')

def request_url(url):
    try:
        headers = {
            'User-Agent': agent
        }
        request = Request('GET', url, headers=headers)

        sleep = random.randint(1, 10)
        if not session.cache.contains(request=request):
            print(f"no cache, sleep {sleep}")
            time.sleep(sleep)
        else:
            print("in cache")

        prepared = session.prepare_request(request)
        response = session.send(prepared)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        print(url)
        page_content = response.text
        return page_content
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def request_page(page: int):
    url = f"https://www.emag.ro/side-by-side/p{page}/c"
    # url = f"https://www.emag.ro/combine-frigorifice/filter/volum-net-total-f8258,401-450-l-v27263/volum-net-total-f8258,451-500-l-v27265/volum-net-total-f8258,peste-600-l-v27266/volum-net-total-f8258,501-600-l-v27276/p{page}/c"
    return request_url(url)

def parse_max_page(soup):
    element = soup.select_one('#listing-paginator li:nth-last-of-type(2) a')

    if not element:
        return None
       
    # Extract and print the text
    return int(element.get_text(strip=True))

def list_products(html: str):
    soup = BeautifulSoup(html, 'html.parser')

    max_page = parse_max_page(soup)

    # #card_grid > div > div > div > div.card-v2-info > div > h2 > a
    products = soup.select('#card_grid > div > div > div > div.card-v2-info > div > h2 > a')
    return products, max_page

def list_depth(html: str) -> float:
    product_soup = BeautifulSoup(html, 'html.parser')

    depth = product_soup.find('td', string='Adancime')
    if not depth:
        print("skipping, could not find depth")
        return None

    sibling = depth.find_next_sibling('td').text

    match = re.search(r'\d+(\.\d+)?', sibling)
    if not match:
        print("Skipping, no regex match")
        return None

    normalised = float(match.group())
    if normalised > 100:
        normalised /= 10

    return normalised

@dataclass
class Fridge:
    depth: float
    url: str


if __name__ == "__main__":
    max_page = 1
    page = 1
    fridges = []
    while page <= max_page:
        html = request_page(page)
        products, max_page = list_products(html)

        for product in products:
            url = product['href']
            html = request_url(url)
            depth = list_depth(html)
            if depth:
                fridges.append(Fridge(url=url,depth=depth))

        page += 1

    sorted_fridges = sorted(fridges, key=lambda f: f.depth)
    for fridge in sorted_fridges:
        print(fridge)

        