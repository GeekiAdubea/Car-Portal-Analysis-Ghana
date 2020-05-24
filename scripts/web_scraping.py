import requests
import argparse
from bs4 import BeautifulSoup
from pymongo import MongoClient
import sys

base_url = 'https://tonaton.com/en/ads/ghana/cars'
page_num = 1

#function to get url of page
def get_page(url):
    page = requests.get(url).text
    return page

#this function will parse to BeautifulSoup and collect all page details
def collect_page_info(url):
    if args.verbose:
        print("Requesting page...")
    page = requests.get(url).text

    #Parsing with BeautifulSoup
    if args.verbose:
        print("Parsing response with BeautifulSoup")
    page_content = BeautifulSoup(page, 'html.parser')

    #HTML tag that contains data I want to scrape
    all_cars = page_content.find_all('a', attrs={'class':'card-link--3ssYv gtm-ad-item'})

    #calling the collect_car_details_and_store_in_mongo function and passing the all_cars variable to it
    collect_car_details_and_store_in_mongo(all_cars)

    #checking if there is more data
    end = page_content.find("div", {"class": "no-result-text--16bWr"})

    if end is None:
        if args.verbose:
            print("On to the next page")
    #if end returns nothing, then there is more data
        global page_num
        page_num += 1
        new_url = base_url + "?page={}".format(page_num)
        collect_page_info(new_url)
    else:
        if args.verbose:
            print("No more data")
        sys.exit(1)
        
#function for scraping data and saving it in MongoDB
def collect_car_details_and_store_in_mongo(content):
    if args.verbose:
        print("Connecting to MongoDB")
    db_client = MongoClient()

    if args.verbose:
        print("Extracting data from response")
    
    #looping through tag we will be scraping 
    for i in content:
    #for each entry
        link = i.get('href')
        new_link = 'http://tonaton.com' + link
        r = requests.get(new_link).text
        r_content = BeautifulSoup(r, 'html.parser')
        #details = r_content.find_all('div', attrs={'class':'two-columns--19Hyo'})

        extract = {}

        listing = r_content.find("h1", attrs={"class":"title--3s1R8"}).text
        extract['Listing'] = listing

        price = r_content.find("div", attrs={"class":"amount--3NTpl"}).text
        extract['Price'] = price

        all_data = r_content.find_all('div', attrs={'class':'two-columns--19Hyo full-width--XovDn justify-content-flex-start--1Xozy align-items-normal--vaTgD flex-wrap-nowrap--3IpfJ flex-direction-row--27fh1 flex--3fKk1'})
        for i in all_data:
            extract[i.find('div', attrs={'class':'word-break--2nyVq label--3oVZK'}).text] = i.find('div', attrs={'class': 'word-break--2nyVq value--1lKHt'}).text
        
        db_client.web_scraping_db.cars_collection.insert_one(extract)

if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-d", "--dryrun", help="dry run mode- no changes", action="store_true")
    arg_parser.add_argument("-v", "--verbose", help="enable verbose output", action="store_true")
    args = arg_parser.parse_args()

    get_page(base_url)
    collect_page_info(base_url)