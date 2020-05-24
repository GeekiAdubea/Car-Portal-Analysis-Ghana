import sys
import logging
import time

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

logging.basicConfig(level=logging.DEBUG)

BASE_URL = 'https://tonaton.com/en/ads/ghana/cars'
page_num = 1

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"}


def get_page(url):
    """
    Function for getting a page using a url.
    Sleep for 1 second before evert request. Just to be good citizens of the internet.
    """
    time.sleep(1)
    page = requests.get(url, headers=HEADERS).text
    return page


def collect_page_info(url):
    """
    This function collects the car items on every page, parses it and 
    calls the function collect_car_details_and_store_in_mongo to retrieve 
    the cars details and store in mongodb.
    """
    logging.info("getting page for url: {}".format(url))
    page = get_page(url)

    #Parsing with BeautifulSoup
    logging.info("Parsing page response with BeautifulSoup")
    page_content = BeautifulSoup(page, 'html.parser')

    #HTML tag that contains data I want to scrape
    all_cars = page_content.find_all('a', attrs={'class':'card-link--3ssYv gtm-ad-item'})

    #calling the collect_car_details_and_store_in_mongo function and passing the all_cars variable to it
    collect_car_details_and_store_in_mongo(all_cars)

    #checking if there is more data
    end = page_content.find("div", {"class": "no-result-text--16bWr"})

    if end is None:
        logging.info("On to the next page")
    #if end returns nothing, then there is more data
        global page_num
        page_num += 1
        new_url = BASE_URL + "?page={}".format(page_num)
        collect_page_info(new_url)
    else:
        logging.info("No more data to scrape")
        sys.exit(1)
        

def collect_car_details_and_store_in_mongo(content):
    """
    This function extracts car details from a page, and saves it in mongodb
    """
    logging.info("Connecting to MongoDB")
    db_client = MongoClient()

    logging.info("Extracting data from details response")
    
    #looping through tag we will be scraping 
    for each in content:
        link = each.get('href')
        new_link = 'http://tonaton.com' + link
        req = get_page(new_link)
        r_content = BeautifulSoup(req, 'html.parser')

        extract = {}

        listing = r_content.find("h1", attrs={"class":"title--3s1R8"}).text
        extract['Listing'] = listing

        price = r_content.find("div", attrs={"class":"amount--3NTpl"}).text
        extract['Price'] = price

       
        all_data = r_content.find_all('div', attrs={'class':'two-columns--19Hyo full-width--XovDn justify-content-flex-start--1Xozy align-items-normal--vaTgD flex-wrap-nowrap--3IpfJ flex-direction-row--27fh1 flex--3fKk1'})
        for i in all_data:
            extract[i.find('div', attrs={'class':'word-break--2nyVq label--3oVZK'}).text] = i.find('div', attrs={'class': 'word-break--2nyVq value--1lKHt'}).text
        
        logging.info("Saving data in mongo")
        db_client.web_scraping_db.cars_collection.insert_one(extract)


if __name__ == "__main__":
    collect_page_info(BASE_URL)
