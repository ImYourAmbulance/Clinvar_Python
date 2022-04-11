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


def parse(url: str):
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
        gene_data.append({
            'Gene link': links[i],
            'Condition': conditions[i],
            'Review Status': review_statuses[i],
            'Clinical Significance': clinical_significances[i]
        })
    return gene_data


raw_url = 'https://www.ncbi.nlm.nih.gov/clinvar/?term='
# TODO: replace that with input variable
combination = "gc"
my_url = raw_url + combination


gene_data = parse(my_url)

client = ApifyClient(os.environ['APIFY_TOKEN'], api_url=os.environ['APIFY_API_BASE_URL'])
#task_client = client.task()
# Get the resource subclient for working with the default dataset of the actor run
default_dataset_client = client.dataset(os.environ['APIFY_DEFAULT_DATASET_ID'])

# Finally, push all the results into the dataset
default_dataset_client.push_items(gene_data)

print(f'Results have been saved to the dataset with ID {os.environ["APIFY_DEFAULT_DATASET_ID"]}')