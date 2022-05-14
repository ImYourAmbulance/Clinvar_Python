import json
import os
from datetime import datetime, time, timedelta, timezone
import os
import re

from apify_client import ApifyClient
from bs4 import BeautifulSoup
import requests

HEADERS = {'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0',
           'accept': '*/*'}

MAIN_PAGE = 0
GENE_MAIN_PAGE = 1
GENE_SCHEME = 2


def parse_page(url: str, page_type: int):
    html = get_html(url)
    if html.status_code == 200:
        return get_content_by_page_type(html, page_type)
    else:
        return -1


def get_html(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_content_by_page_type(html, page_type):
    try:
        if page_type == MAIN_PAGE:
            return parse_content_main_page(html.content)
        elif page_type == GENE_MAIN_PAGE:
            return parse_content_gene_main_page(html.content)
        elif page_type == GENE_SCHEME:
            return parse_content_gene_scheme(html.content)
    except:
        print(f"Error occurred while parsing a page with type = {page_type}")


def parse_content_main_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('tr', class_="rprt")
    tags_with_links = soup.find_all('a', class_="blocklevelaintable variant_title")

    links = [("https://www.ncbi.nlm.nih.gov" + tag['href'])
            for tag in tags_with_links]

    conditions = [tag.get_text()
                for tag in soup.find_all('td', class_='docsum_table_condition')]

    review_statuses = [rprt_item.find_all('td')[-2].get_text()
                    for rprt_item in items]

    clinical_significances = [rprt_item.find_all('td')[-3].get_text()
                            for rprt_item in items]

    gene_data = []

    for i in range(len(items)):
        additional_info = parse_page(links[i], GENE_MAIN_PAGE)
        gene_data.append({
            'Gene link': links[i],
            'Condition': conditions[i],
            'Review Status': review_statuses[i],
            'Clinical Significance': clinical_significances[i]
            # , 'Additional Info' : additional_info
        })
    return gene_data


def parse_content_gene_main_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find_all("table", class_="hgvstable stickyheaders")
    gene_picture_tag = soup.find_all("a", {'href': True, 'target': "_blank", "data-section": "variant details",
                                           "data-ga-action": "HGVS"})[0]
    gene_picture_link = gene_picture_tag["href"]
    parse_page(gene_picture_link, GENE_SCHEME)


def parse_content_gene_scheme(html):
    soup = BeautifulSoup(html, 'html.parser')
    print(soup)


def parse_main_page(url: str):
    html = get_html(url)
    if html.status_code == 200:
        return parse_content_main_page(html.content)
    else:
        return list()


if __name__ == "__main__":
    client = ApifyClient(os.environ['APIFY_TOKEN'], api_url=os.environ['APIFY_API_BASE_URL'])
    default_kv_store_client = client.key_value_store(os.environ['APIFY_DEFAULT_KEY_VALUE_STORE_ID'])
    search_term = default_kv_store_client.get_record(os.environ['APIFY_INPUT_KEY'])['value']['search_term']
    raw_url = 'https://www.ncbi.nlm.nih.gov/clinvar/?term='
    my_url = raw_url + search_term
    gene_data = parse_page(my_url, MAIN_PAGE)

    # test_link = "https://www.ncbi.nlm.nih.gov/clinvar/variation/732690/"
    # parse_gene_page_2(link)
    default_dataset_client = client.dataset(os.environ['APIFY_DEFAULT_DATASET_ID'])

    # Finally, push all the results into the dataset
    default_dataset_client.push_items(gene_data)
    print(f'Results have been saved to the dataset with ID {os.environ["APIFY_DEFAULT_DATASET_ID"]}')
