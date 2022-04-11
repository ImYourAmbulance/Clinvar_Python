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

def get_html(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def parse_gene_page_2(url: str):
    html = get_html(url)
    if html.status_code == 200:
        return get_content_gene_2(html.content)
    else:
        print(f"Cant get the html from page {url}")


def parse_gene_page_1(url):
    html = get_html(url)
    if html.status_code == 200:
        return get_content_gene_1(html.content)
    else:
        print(f"Cant get the html from page {url}")

def parse_main_page(url: str):
    html = get_html(url)
    if html.status_code == 200:
        return get_content(html.content)
    else:
        return list()


def get_content(html):
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
        #additional_info = parse_gene_page_1(links[i])

        gene_data.append({
            'Gene link': links[i],
            'Condition': conditions[i],
            'Review Status': review_statuses[i],
            'Clinical Significance': clinical_significances[i]
        })
    return gene_data


def get_content_gene_1(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find_all("table", class_="hgvstable stickyheaders")
    gene_picture_tag = soup.find_all("a",{'href': True, 'target': "_blank", "data-section": "variant details",
                                   "data-ga-action": "HGVS"})[0]
    gene_picture_link = gene_picture_tag["href"]
    parse_gene_page_2(gene_picture_link)


def get_content_gene_2(html):
    soup = BeautifulSoup(html, 'html.parser')
    print(soup)

if __name__ == "__main__":
    client = ApifyClient(os.environ['APIFY_TOKEN'], api_url=os.environ['APIFY_API_BASE_URL'])
    
    default_kv_store_client = client.key_value_store(os.environ['APIFY_DEFAULT_KEY_VALUE_STORE_ID'])
    search_term = default_kv_store_client.get_record(os.environ['APIFY_INPUT_KEY'])['value']['search_term']

    raw_url = 'https://www.ncbi.nlm.nih.gov/clinvar/?term='
    my_url = raw_url + search_term
    print(f'Looking for {my_url}')
    
    gene_data = parse_main_page(my_url)
    # test_link = "https://www.ncbi.nlm.nih.gov/clinvar/variation/732690/"
    #parse_gene_page_2(link)

    default_dataset_client = client.dataset(os.environ['APIFY_DEFAULT_DATASET_ID'])
    # Finally, push all the results into the dataset
    default_dataset_client.push_items(gene_data)

    print(f'Results have been saved to the dataset with ID {os.environ["APIFY_DEFAULT_DATASET_ID"]}')
