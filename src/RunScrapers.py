import sys
# from pymongo import MongoClient
from NewspaperScraper import *
import os

# client = MongoClient()
# db = client.News_database


def run_scraper(agency, scraper):
    scraper.get_pages()
    data = scraper.get_articles()
    folder_name = "data"
    # Create the 'data' folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    # Create the filename as 'agency.csv' inside the 'data' folder
    filename = os.path.join(folder_name, f"{agency}.csv")
    scraper.write_to_csv(data, filename)


def initialize_scraper (agency):
    if agency == 'Fox News':
        run_scraper(agency, FoxNewsScraper(agency))
    elif agency == 'Wall Street Journal':
        run_scraper(agency, WSJScraper(agency))
    elif agency == 'New York Times':
        run_scraper(agency, NYTScraper(agency))
    elif agency == 'CNN':
        run_scraper(agency, CNNScraper(agency))
    elif agency == 'Vox':
        run_scraper(agency, VoxScraper(agency))
    elif agency == 'AlJazeera':
        run_scraper(agency, AlJazeeraScraper(agency))
    elif agency == 'BBC':
        run_scraper(agency, BBCScraper(agency))
    elif agency == 'TheAtlantic':
        run_scraper(agency, AtlanticScraper(agency))
    elif agency == 'HuffPost':
        run_scraper(agency, HuffPostScraper(agency))


if __name__ == "__main__":
    news_agencies = ['Fox News','Wall Street Journal','CNN','Vox','BBC','TheAtlantic']
    for agency in news_agencies:            
        initialize_scraper(agency)
