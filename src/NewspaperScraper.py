import re
import csv
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from dateutil import parser
from pytz import timezone, UnknownTimeZoneError
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from dateutil.parser import parse
from newspaper import Article
from newspaper import Config
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import re
import os
from urllib.parse import urljoin



class NewspaperScraper:
    def __init__ (self, newspaper):
        self.newspaper = newspaper
        self.searchTerm = ['Palestine','Israel','Gaza','Hamas']
        self.dateStart = datetime(2023, 10, 1)
        self.dateEnd = date.today()
        self.links = []

    def get_newspaper_name (self):
        return self.newspaper

    def get_pages (self):
        # print 'Unimplemented for ' + self.newspaper + ' scraper'
        return


    def write_to_csv (self, data, filename):
        print('writing to CSV...')
        # Assuming 'df' is your DataFrame
        data.to_csv(filename, index=False)


#     def write_to_mongo (self, data, collection):
#         print 'writing to mongoDB...'
#         count = 0

#         for d in data:
#             collection.insert(d)
#             count += 1
#             print count


class NewspaperScraperWithAuthentication(NewspaperScraper):
    def __init__ (self, newspaper):
        NewspaperScraper.__init__(self, newspaper)
        _ = load_dotenv(find_dotenv())


        if newspaper == 'New York Times':
            self.userId = os.environ.get('NYT_USERNAME')
            self.password = os.environ.get('NYT_PASS')
        elif newspaper == 'Wall Street Journal':
            self.userId = os.environ.get('WSJ_USERNAME')
            self.password = os.environ.get('WSJ_PASS')



class BBCScraper(NewspaperScraper):
    def get_pages(self, sleep_time=3):
        print('ruuning get_pages() for BBC...')
        links = []
        count = 0
        page_num = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 60)
        url = 'https://www.bbc.com/news/topics/c207p54m4rqt'
        base_url = 'https://www.bbc.com'
        browser.get(url)
        time.sleep(7)
        while True and page_num < 35:
            try:
                a_xpath = '//div[@id="__next"]//main//section[@data-testid="alaska-section-outer"]//a'
                a_tags = wait.until(EC.presence_of_all_elements_located((By.XPATH, a_xpath)))
                for tag in a_tags:
                    href_value = tag.get_attribute('href')
                    link = urljoin(base_url, href_value)
                    print(link)
                    links.append(link)
                    count += 1
                next_page_button_xpath = '//button[@data-testid="pagination-next-button"]'
                next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, next_page_button_xpath)))
                next_page_button.click()
                page_num +=1
                time.sleep(4)
            except (TimeoutException, WebDriverException,NoSuchElementException):
                print("some error")
                break
            
            except Exception as e:
                print(f"Exception: {e}")
                break
        browser.quit()
        links = list(set(links))
        print('Total Count:', len(links))
        self.links = links
        return
    
    
    def get_articles(self, sleep_time=3):
        print('getting BBC articles...')
        results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text','url'])
        count = 0
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
            'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
        ]
        
        for l in self.links:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in headless mode (without GUI)
            chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration
            # chrome_options.add_argument('--no-sandbox')  # Disable sandboxing for Linux
            chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
            port = 4444
            driver = webdriver.Chrome(options=chrome_options, port=port)
            time.sleep(20)
            
            try:
                driver.get(l)
                html_source = driver.page_source
                time.sleep(10)
                driver.quit()
                print('retrieved url')
                soup = BeautifulSoup(html_source, 'html.parser')

                title=None
                title_elements = soup.find_all('title')
                if title_elements:
                    first_title_element = title_elements[0]
                    title = first_title_element.get_text(strip=True)
                print("title:",title)
                
                authors = soup.find('span', {'data-testid':'byline-name'})
                if authors:
                    authors = authors.get_text(strip=True)
                print("author:",authors)
                
                published_date = soup.find('time')
                if published_date:
                    published_date = published_date.get_text(strip=True)
                    print("Text yes:", published_date)
                else:
                    published_date = soup.find('span', class_=lambda x: x and 'sc-5962' in x)
                    if published_date:
                        published_date = published_date.get_text(strip=True)
                if published_date:
                    try:
                        date_part, time_part = published_date.split(',', 2)
                        parsed_date = parser.parse(date_part)
                        published_date = parsed_date.strftime('%Y-%m-%d')
                    except Exception as e:
                        if "hours ago" in e:
                            published_date = published_date.get_attribute('datetime')
                            published_date = published_date.split('T')[0]
                print("Date:",published_date)            

                content = ""
                section_element = soup.find_all('section',{'data-component':'text-block'})
                for section in section_element:
                    p_element = section.find('p')
                    if p_element:
                        para = p_element.get_text(strip=True)
                        content += para + '\n'
                
                if content =="":
                    p_tags = soup.find_all('p', class_=lambda x: x and 'sc-eb7bd' in x)
                    if p_tags:
                        for p in p_tags:
                            if p:
                                para = p.get_text(strip=True)
                                content += para + '\n'
                # print("content:",content)
                
                
                data = {
                    'title': title,
                    'date_published': published_date,
                    'news_outlet': self.newspaper,
                    'authors': authors,
                    'text': content,
                    'url':l
                }
                
                df_dictionary = pd.DataFrame([data])
                results = pd.concat([results, df_dictionary], ignore_index=True)
                print(l)
                # print(data['title'])
                # print(data['text'])
                # print(data['date_published'])
                # print(data['authors'])
                # print(data['news_outlet'])
                count += 1
                print(count)
                
            except Exception as e:
                print(f"An error occurred: {e} for link: {l}") 
                continue

        # browser.close()
        print("Count: ",count)
        return results

            
            
        
        
class AlJazeeraScraper(NewspaperScraper):
    def get_pages(self, sleep_time=3):
        print('running get_pages()...')
        links = []
        count = 0
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124  Safari/537.36'}
        chrome_options = Options()
        # chrome_options.add_argument('--headless') 
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 60)
        for keyword in self.searchTerm:
            url = str('https://www.aljazeera.com/search/'
                        +keyword
                        +'?sort=date')
            print(url)
            browser.get(url)
            
            a_xpath = '//a[contains(@class, "u-clickable-card__link")]'
            while True:
                try:
                    show_more_button_xpath = '//button[@class="show-more-button grid-full-width"]'
                    show_more_button = wait.until(EC.element_to_be_clickable((By.XPATH, show_more_button_xpath)))
                    browser.execute_script("arguments[0].scrollIntoView();", show_more_button)
                    time.sleep(5)
                    show_more_button.click()

                except Exception as e:
                    print(f"Error:{e}")
                    break 
            a_tags = wait.until(EC.visibility_of_all_elements_located((By.XPATH, a_xpath)))
            for a in a_tags:
                link = a.get_attribute('href')
                links.append(link)
                print(link)
                count +=1
                print(count)
            time.sleep(20)
                
        links = list(set(links))
        print("Total number of links:", len(links))
        self.links = links 
        return
    
    def get_articles(self, sleep_time=3):
        print('getting articles...')
        results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text'])
        count = 0
        for l in self.links:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(l, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')

                title_element = soup.find('title', {'data-reactroot': True})
                # Get the text content of the title
                title = title_element.get_text(strip=True) if title_element else None


                meta_element = soup.find('meta', {'name': 'displayAuthors'})
                # Get the content attribute value
                authors = meta_element['content'] if meta_element else None


                meta_element = soup.find('meta', {'name': 'publishedDate'})
                # Get the content attribute value
                published_date = meta_element['content'] if meta_element else None


                div_element = soup.find('div', class_='wysiwyg wysiwyg--all-content css-ibbk12')
                # Extract all <p> tags from the div
                p_tags = div_element.find_all('p')
                # Initialize a larger string to append the content
                larger_string = ""
                # Append the text content of each <p> tag to the larger string
                for p_tag in p_tags:
                    larger_string += p_tag.get_text(strip=True) + '\n'

                data = {
                    'title': title,
                    'date_published': published_date,
                    'news_outlet': self.newspaper,
                    'authors': authors,
                    'text': larger_string,
                }
                df_dictionary = pd.DataFrame([data])
                results = pd.concat([results, df_dictionary], ignore_index=True)
                print(data['title'])
                print(data['text'])
                print(data['date_published'])
                print(data['authors'])
                print(data['news_outlet'])
                count += 1
                print(count)

            except Exception as e:
                print(f"An error occurred: {e} for link: {l}") 
                continue

        # browser.close()
        print("Count: ",count)
        return results
            
            
        

class FoxNewsScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')
        start_date_str = self.dateStart.strftime("%m-%d-%Y")  # Replace this with self.dateStart
        start_date = datetime.strptime(start_date_str, "%m-%d-%Y").date()
        end_date = date.today()
        links = []
        count = 0
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124  Safari/537.36'}
        for keyword in self.searchTerm:
            chrome_options = Options()
            chrome_options.add_argument('--headless') 
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 60)
            url = "https://www.foxnews.com/search-results/search"
            driver.get(url)
            date_range_element = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.filter.date-range'))
            )

            # Find the search input field and input the keyword
            search_input = driver.find_element_by_css_selector('.main-search input[type="text"]')
            search_input.send_keys(keyword)

            # Scroll down to make the dropdown options visible
            driver.execute_script("arguments[0].scrollIntoView();", date_range_element)

            date_range_element.find_element_by_css_selector('.sub.month button').click()
            month_to_select = start_date.strftime("%m")
            # Find and click on the specific option for the month
            month_option_xpath = f'.//li[@id="{month_to_select}" and ancestor::div[contains(@class, "month")] and ancestor::div[contains(@class, "min")]]'
            wait.until(EC.element_to_be_clickable((By.XPATH, month_option_xpath))).click()

            date_range_element.find_element_by_css_selector('.sub.day button').click()
            day_to_select = start_date.strftime("%d")
            # Find and click on the specific option for the month
            day_option_xpath = f'.//li[@id="{day_to_select}" and ancestor::div[contains(@class, "day")] and ancestor::div[contains(@class, "min")]]'
            wait.until(EC.element_to_be_clickable((By.XPATH, day_option_xpath))).click()

            date_range_element.find_element_by_css_selector('.sub.year button').click()
            year_to_select = start_date.strftime("%Y")
            # Find and click on the specific option for the month
            year_option_xpath = f'.//li[@id="{year_to_select}" and ancestor::div[contains(@class, "year")] and ancestor::div[contains(@class, "min")]]'
            wait.until(EC.element_to_be_clickable((By.XPATH, year_option_xpath))).click()


            search_button = driver.find_element_by_css_selector('.main-search .button a')
            search_button.click()
            time.sleep(sleep_time)
            while True:
                try:
                    # Wait for the "Load More" button to be clickable
                    load_more_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.button.load-more'))
                    )

                    # Click the "Load More" button
                    load_more_button.click()
                    time.sleep(sleep_time)
                except (TimeoutException, NoSuchElementException):
                    # Break the loop if the button is not found or not clickable
                    break


            articles = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article.article'))
            )
            for article in articles:
                try:
                    # Find the first <a> tag inside the article
                    link = article.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    # Append the link to the list
                    links.append(link)
                    count += 1
                except NoSuchElementException:
                    # Continue to the next article if no <a> tag is found
                    continue
            driver.close()
        links = list(set(links))
        print("Links:")
        print(links)
        print("Total number of links:", len(links))
        self.links = links 
        return
    
    def get_articles(self, sleep_time=3):
        print('running get_articles()...')
        results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text'])
        count = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 50)
        for l in self.links:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(l, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')

                title = soup.find('title').get_text()

                authors = []
                author_div = soup.find('div', {'class': 'author-byline'})
                if author_div:
                    span_tags = author_div.find_all('span')
                    for s_tags in span_tags:
                        span_text = s_tags.get_text(strip=True)
                        if "By" in span_text:
                            children = s_tags.find_all('span', recursive=False)
                            for child in children:
                                author = child.find('a').get_text(strip=True)
                                authors.append(author)

                time_tag = soup.find('time')
                date_string = time_tag.get_text() if time_tag else ''
                parsed_date = parser.parse(date_string)
                formatted_date = parsed_date.strftime('%Y-%m-%d')

                content = ""
                div_element = soup.find('div', class_=lambda x: x and 'article-body' in x)
                if div_element:
                    for p_tag in div_element.find_all('p'):
                        para = p_tag.get_text()
                        content += para + '\n'

                data = {
                    'title': title,
                    'date_published': formatted_date,
                    'news_outlet': self.newspaper,
                    'authors': authors,
                    'text': content,
                }
                df_dictionary = pd.DataFrame([data])
                results = pd.concat([results, df_dictionary], ignore_index=True)
                print(data['title'])
                print(data['text'])
                print(data['date_published'])
                print(data['authors'])
                print(data['news_outlet'])
                count += 1
                print(count)

            except Exception as e:
                print(f"An error occurred: {e} for link: {l}") 
                continue
                
        browser.close()
        print("Count: ",count)
        return results
    
    

    
    
    
class VoxScraper(NewspaperScraper):
    def get_pages(self):
        print('running get_pages()...')
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        browser = webdriver.Chrome(options=chrome_options)
        indices = [0,100,200,300,400,500]
        links = []
        page_num = 1
        count = 0
        stop = False
        for keyword in self.searchTerm:
            while not stop and page_num<20:
                url = str('https://www.vox.com/search?order=date&q='
                        +keyword
                        +'&page='
                        +str(page_num)
                        +'&type=Article')
                page_num = page_num+1
                browser.get(url)
                print(url)
                article_xpath = './/h2[contains(@class, "c-entry-box--compact__title")]'
                
                article_elements = WebDriverWait(browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, article_xpath)))
                # Loop through each article element and extract the href value
                for article_element in article_elements:
                    try:
                        # Use relative XPath to find the <a> element within the h2
                        a_element = article_element.find_element(By.XPATH, './a')
                        # Extract the href attribute
                        href_value = a_element.get_attribute('href')
                        # Print or store the href value as needed
                        # print("href:", href_value)
                        links.append(href_value)
                        count = count+1
                        # print(count)
                    except NoSuchElementException:
                        print('No <a> element found within the h2')
                        continue
                    except Exception as e:
                        print(f"Error: {e}")
                        break
        
        browser.quit()
        links = list(set(links))
        print("Total number of links:", len(links))
        self.links = links
        return
        
    def get_articles(self, sleep_time=3):
        print('running get_articles()...')
        results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text'])
        count = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 50)
        for l in self.links:
            try:
                print(l)
                browser.get(l)

                # Wait until the page is loaded or raise a TimeoutException
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/head/title'))
                )

                page_html = browser.page_source
                soup = BeautifulSoup(page_html, 'html.parser')
                
                title = soup.find('title').get_text()
                meta_tag = soup.find('meta', {'property': 'og:title'})
                if meta_tag:
                    title = meta_tag['content']
                    
                date_published = None
                meta_tag = soup.find('meta', {'property': 'article:published_time'})
                if meta_tag:
                    date_published = meta_tag['content']
                    date_published = date_published.split('T')[0]

                authors = []
                meta_tag = soup.find_all('meta', {'property': 'author'})
                print(meta_tag)
                for tag in meta_tag:
                    authors.append(tag['content'])


                # def is_p_under_main(tag):
                #     return tag.name == 'p' and tag.find_parent('main')
                
                p_tags = soup.find_all('p')
                extracted_text = ""
                # Now, you can iterate over the found <p> tags
                for p_tag in p_tags:
                    # Do something with the <p> tag
                    if p_tag.find_parent('div', class_='c-article-footer c-article-footer-cta'):
                        continue
                    if p_tag.find_parent('div', class_='c-newsletter_signup_box--form__error'):
                        continue
                    main_ancestor = p_tag.find_parent('main')
                    if main_ancestor:
                        print(p_tag.text)
                        extracted_text += p_tag.get_text() #+ '\n'

                data = {
                    'title': title,
                    'date_published': date_published,
                    'news_outlet': self.newspaper,
                    'authors': authors,
                    'text': extracted_text,
                }
                df_dictionary = pd.DataFrame([data])
                results = pd.concat([results, df_dictionary], ignore_index=True)
                print(data['title'])
                print(data['text'])
                print(data['date_published'])
                print(data['authors'])
                print(data['news_outlet'])
                time.sleep(sleep_time)
                count+=1
            
            except TimeoutException as te:
                print(f"TimeoutException")
                break
            except Exception as e:
                print(f"Exception: {e}")
                continue  
        browser.close()
        print("Count: ", count)
        return results


    
    
# class ReutersScraper(NewspaperScraper):
#     def get_pages(self, sleep_time=3):
#         print('running get_pages()...')
#         chrome_options = Options()
#         # chrome_options.add_argument('--headless') 
#         chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
#         driver = webdriver.Chrome(options=chrome_options)
#         wait = WebDriverWait(driver, 30)
#         links = []
#         stop = False
#         count = 0

#         for keyword in self.searchTerm:
#             url = str('https://www.reuters.com/site-search/?query='
#                       + keyword
#                       +'&date=past_year&offset=0&sort=newest')
#             driver.get(url)
#             while not stop:
#                 try:
#                     h3_elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'h3')))
#                     print('found h3_elements')
#                     print("h3:",h3_elements[0].text)
#                     for h3_element in h3_elements:
#                         try:
#                             # Check if 'div' is in the parent chain
#                             ancestor_elements = h3_element.find_elements(By.XPATH, './ancestor::div[@class,"search-results"]')
#                             if ancestor_elements:
#                                 # Find <a> tag inside h3
#                                 a_element = h3_element.find_element(By.XPATH, './/a')
#                                 # print("text:", a_element.text)
#                                 # Extract href attribute
#                                 href_value = a_element.get_attribute('href')
#                                 print("href:", href_value)
#                                 links.append(href_value)
#                         except NoSuchElementException:
#                             print('No such element')
#                             # Continue to the next h3_element if 'article' is not found in the ancestor chain
#                             continue   
#                         except Exception as E:
#                             print(f"Error: {e}")
#                             break
                                
#                     next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@class="button__button__2Ecqi button__secondary__18moI"]')))

#                     next_page_button.click() 
#                     time.sleep(random.uniform(3, 5))
#                 except (TimeoutException, WebDriverException,NoSuchElementException):
#                     # Handle the case where the URL does not exist or fails to load
#                     # print(f"Failed to load URL: {url}")
#                     stop = True
#                     break
#                     # Close the WebDriver
#                     driver.quit()

#         links = list(set(links))
#         print("Total number of links:", len(links))
#         self.links = links
#         return            
            
#     def get_articles(self, sleep_time=3):
#         print('running get_articles()...')
#         results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text'])
#         count = 0
#         chrome_options = Options()
#         chrome_options.add_argument('--headless') 
#         chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
#         browser = webdriver.Chrome(options=chrome_options)
#         wait = WebDriverWait(browser, 50)
#         for l in self.links:
#             print(l)
#             browser.get(l)
#             page_html = browser.page_source
#             soup = BeautifulSoup(page_html, 'html.parser')
#             date_published = None
#             meta_tag = soup.find('meta', {'name': 'article:published_time'})
#             if meta_tag:
#                 date_published = meta_tag['content']
#                 date_published = date_published.split('T')[0]  
#             authors = []
#             meta_tag = soup.find_all('meta', {'name': 'article:author'})
#             for tag in meta_tag:
#                 authors.append(tag['content']) 
#             title = soup.find('title').get_text()      

#             def is_p_under_main(tag):
#                 return tag.name == 'p' and tag.find_parent('main')
#             # Find all <p> tags that satisfy the filter condition
#             p_tags_under_main = soup.find_all(is_p_under_main)
#             extracted_text = ""
#             # Now, you can iterate over the found <p> tags
#             for p_tag in p_tags_under_main:
#                 # Do something with the <p> tag
#                 print(p_tag.text)
#                 extracted_text += p.get_text() #+ '\n'
                
                
#             data = {
#                 'title': title,
#                 'date_published': date_published,
#                 'news_outlet': self.newspaper,
#                 'authors': authors,
#                 'text': extracted_text,
#             }
#             df_dictionary = pd.DataFrame([data])
#             results = pd.concat([results, df_dictionary], ignore_index=True)
#             print(data['title'])
#             print(data['text'])
#             print(data['date_published'])
#             print(data['authors'])
#             print(data['news_outlet'])
#             # print()
#             # print()
#             time.sleep(sleep_time)
#             count += 1
#         browser.close()
#         print("Count: ",count)
#         return results
            
            
            
class CNNScraper(NewspaperScraper):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        browser = webdriver.Chrome(options=chrome_options)
        indices = [0,100,200,300,400,500]
        links = []
        index = 0
        count = 0
        url = 'https://www.cnn.com/search?q='
        browser.get(url)
        for keyword in self.searchTerm:
            for index in indices:
                url = str(f'http://www.cnn.com/search?q=' 
                          + keyword 
                          + '&from=' + str(index)
                          + '&sort=newest'
                          + '&types=article'
                          + '&size=100')
                
                new_params = {'q': keyword, 'from': str(index),'sort':'newest','types':'article','size':'100'}
                script = "window.location.search = '?{}';".format('&'.join([f'{key}={value}' for key, value in new_params.items()]))
                print(script)
                browser.execute_script(script)
                updated_url = browser.current_url
                browser.get(updated_url)
                print(updated_url)
                time.sleep(5)
                
                article_xpath = './/a[contains(@class, "container__link")]'
                article_elements = WebDriverWait(browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, article_xpath)))
            
                # Loop through each article element and extract the href value
                for article_element in article_elements:
                    print("Article:",article_element)
                    href_value = article_element.get_attribute('href')
                    links.append(href_value)
                    count = count+1
                    print(count,": ",href_value)
            browser.close()
        links = list(set(links))
        print("Total number of links:", len(links))
        self.links = links
        return 

    def get_articles(self, sleep_time=3):
        print('running get_articles()...')
        results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text'])
        count = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 50)

        for l in self.links:
            try:
                print(l)
                browser.get(l)

                # Wait until the page is loaded or raise a TimeoutException
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/head/title'))
                )

                page_html = browser.page_source
                soup = BeautifulSoup(page_html, 'html.parser')

                date_published = None
                meta_tag = soup.find('meta', {'property': 'article:published_time'})
                if meta_tag:
                    date_published = meta_tag['content']
                    date_published = date_published.split('T')[0]

                authors = []
                meta_tag = soup.find_all('meta', {'name': 'author'})
                for tag in meta_tag:
                    authors.append(tag['content'])

                title = soup.find('title').get_text()
                meta_tag = soup.find('meta', {'property': 'og:title'})
                if meta_tag:
                    title = meta_tag['content']

                # Find all <p> tags inside the <div> tag
                paragraphs = soup.find_all('p', class_='paragraph inline-placeholder')

                # Initialize a variable to store the extracted text from <p> tags
                extracted_text = ""

                # Concatenate the text from each <p> tag
                for p in paragraphs:
                    print(p.get_text())
                    extracted_text += p.get_text()

                data = {
                    'title': title,
                    'date_published': date_published,
                    'news_outlet': self.newspaper,
                    'authors': authors,
                    'text': extracted_text,
                }
                df_dictionary = pd.DataFrame([data])
                results = pd.concat([results, df_dictionary], ignore_index=True)
                print(data['title'])
                print(data['text'])
                print(data['date_published'])
                print(data['authors'])
                print(data['news_outlet'])
                time.sleep(sleep_time)
                count += 1
            
            except TimeoutException as te:
                print(f"TimeoutException")
                break
            except Exception as e:
                print(f"Exception: {e}")
                continue
                
        browser.close()
        print("Count: ", count)
        return results
    
    
    
    
    


class WSJScraper(NewspaperScraperWithAuthentication):
    def get_pages (self, sleep_time=3):
        print('running get_pages()...')
        links = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124  Safari/537.36'}
        chrome_options = Options()
        # chrome_options.add_argument('--headless') 
        for keyword in self.searchTerm:
            stop = False
            index = 1
            driver = webdriver.Chrome(options=chrome_options)
            url= str('http://www.wsj.com/search/term.html?KEYWORD='
                        + keyword
                        + '&startDate=' + str(self.dateStart).replace('-', '/')
                        + '&endDate=' + str(self.dateEnd).replace('-', '/')  
                        + '&page=' + str(index)
                        + '&isAdvanced=true&daysback=4y&andor=AND&sort=date-desc&source=wsjie')

            while not stop:
                print(index)
                # Create a WebDriver instance (in this example, I'm using Chrome)
                index = index + 1
                print(url)
                try:
                    # Navigate to the URL
                    driver.get(url)
                    # Use WebDriverWait to wait for the page to load (adjust the timeout as needed)
                    wait = WebDriverWait(driver, 30)
                    h3_elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'h3')))
                    print('found h3_elements')
                    articles = driver.find_element(By.TAG_NAME, 'article')
                    print('found article')
                    if not articles:
                        print("No articles found. Exiting...")
                        driver.quit()
                        break
                    print("h3:",h3_elements[0].text)
                    for h3_element in h3_elements:
                        try:
                            # Check if 'article' is in the parent chain
                            ancestor_elements = h3_element.find_elements(By.XPATH, './ancestor::article')
                            if ancestor_elements:
                                # Find <a> tag inside h3
                                a_element = h3_element.find_element(By.XPATH, './/a')
                                # print("text:", a_element.text)
                                # Extract href attribute
                                href_value = a_element.get_attribute('href')
                                # print("href:", href_value)
                                links.append(href_value)
                        except NoSuchElementException:
                            # Continue to the next h3_element if 'article' is not found in the ancestor chain
                            continue   
                    next_page_button = wait.until(EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "button") and contains(@class, "pagination") and .//*[contains(text(), "Next Page")]]')))
                    url = next_page_button.get_attribute('href')
                            # Click the "Next Page" button
                    # next_page_button.click()    
                except (TimeoutException, WebDriverException,NoSuchElementException):
                    # Handle the case where the URL does not exist or fails to load
                    # print(f"Failed to load URL: {url}")
                    stop = True
                    break
                    # Close the WebDriver
                    driver.quit()
                
        links = list(set(links))
        print("Links:")
        print(links)
        self.links = links
        return links 
    
    def get_articles(self, sleep_time=0):
        print('running newspaper_parser()...')
        results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text'])
        count = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 50)
        browser.get("https://id.wsj.com/access/pages/wsj/us/signin.html")
        username_field = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,'#username')))
        # Send keys to the username field
        username_field.send_keys(self.userId)
        continue_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="basic-login"]/div[1]/form/div[2]/div[6]/div[1]/button[2]')))  
        continue_button.click()
        element = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, ' //*[@id="password-login-password"]')))
        # Now, you can interact with the element
        element.send_keys(self.password)
        submit_button = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="password-login"]/div/form/div/div[5]/div[1]/button')))
        submit_button.click() 
        time.sleep(15)
        for l in self.links:
            browser.get(l)
            page_html = browser.page_source
            # soup = BeautifulSoup(page.text, 'html.parser')
            article = Article(url='')
            article.set_html(str(page_html))
            # article.download()
            article.html
            article.parse()
            metadata_dict = article.meta_data
            # Extract the publication date from the metadata
            publication_date = metadata_dict.get('article.published', None)
            data = {
                'title': article.title,
                'date_published': publication_date,
                'news_outlet': self.newspaper,
                'authors': article.authors,
                'text': article.text,
            }
            df_dictionary = pd.DataFrame([data])
            results = pd.concat([results, df_dictionary], ignore_index=True)
            time.sleep(sleep_time)
            count += 1
        browser.close()
        return results

    
    
    

class AtlanticScraper(NewspaperScraper):
    def get_pages(self, sleep_time=3):
        print('ruuning get_pages() for the Atlantic...')
        links = []
        count = 0
        page_num = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        browser = webdriver.Chrome(options=chrome_options)
        base_url = "https://www.theatlantic.com"
        wait = WebDriverWait(browser, 60)
        for keyword in self.searchTerm:
            url = 'https://www.theatlantic.com/search/?q='+keyword+'&search-sort=newestToOldest'
            page_num = 1
            while True and page_num < 20:
                browser.get(url)
                try:
                    a_xpath = '//li[@class="SharedResults_searchResultsListItem__k7H0x"]//div//a[@class="SharedResults_titleLink__h2Tp5"]'
                    a_tags = wait.until(EC.presence_of_all_elements_located((By.XPATH, a_xpath)))
                    for tag in a_tags:
                        link = tag.get_attribute('href')
                        print(link)
                        links.append(link)
                        count += 1
                        
                    more_button_xpath = '//a[@class="Pagination_paginationLink__WJhzW" and @data-event-element="more"]'
                    more_button = wait.until(EC.element_to_be_clickable((By.XPATH, more_button_xpath)))
                    url = more_button.get_attribute('href')
                    url = urljoin(base_url, url)
                    page_num +=1
                    time.sleep(4)
                    
                except (TimeoutException, WebDriverException,NoSuchElementException):
                    print("some error")
                    break

                except Exception as e:
                    print(f"Exception: {e}")
                    break
                    
        browser.quit()
        links = list(set(links))
        print('Total Count:', len(links))
        self.links = links
        return
    
    def get_articles(self, sleep_time=3):
        print('running get_articles()...')
        results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text'])
        count = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 50)

        for l in self.links:
            try:
                print(l)
                browser.get(l)

                # Wait until the page is loaded or raise a TimeoutException
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, '/html/head/title'))
                )

                page_html = browser.page_source
                soup = BeautifulSoup(page_html, 'html.parser')

                date_published = None
                meta_tag = soup.find('meta', {'property': 'article:published_time'})
                if meta_tag:
                    date_published = meta_tag['content']
                    date_published = date_published.split('T')[0]

                authors = []
                meta_tag = soup.find_all('meta', {'name': 'author'})
                for tag in meta_tag:
                    authors.append(tag['content'])

                meta_tag = soup.find('meta', {'property': 'og:title'})
                if meta_tag:
                    title = meta_tag['content']

                # Find all <p> tags inside the <div> tag
                content=""
                paragraphs = soup.find_all('p', class_='ArticleParagraph_root__4mszW')
                for par in paragraphs:
                    content += par.get_text(strip=True)

                data = {
                    'title': title,
                    'date_published': date_published,
                    'news_outlet': self.newspaper,
                    'authors': authors,
                    'text': content,
                }
                df_dictionary = pd.DataFrame([data])
                results = pd.concat([results, df_dictionary], ignore_index=True)
                print(data['title'])
                print(data['text'])
                print(data['date_published'])
                print(data['authors'])
                print(data['news_outlet'])
                time.sleep(sleep_time)
                count += 1
            
            except TimeoutException as te:
                print(f"TimeoutException")
                break
            except Exception as e:
                print(f"Exception: {e}")
                continue
                
        browser.close()
        print("Count: ", count)
        return results
    
    
    
    
    
    
class HuffPostScraper(NewspaperScraper):
    def get_pages(self, sleep_time=3):
        print('ruuning get_pages() for HuffPost...')
        links = []
        count = 0
        page_num = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 100)
        url = 'https://www.huffpost.com/news/topic/israeli-palestinian-conflict'
        base_url = 'https://www.huffpost.com'
        browser.get(url)
        time.sleep(7)
        while True and page_num < 25:
            try:
                a_xpath = '//a[contains(@class,"card__headline") and ancestor::div[contains(@class, "js-cet-unit-main")] and not (ancestor::div[@class="a-page__content a-page__content--trending"])]'
                a_tags = wait.until(EC.presence_of_all_elements_located((By.XPATH, a_xpath)))
                for tag in a_tags:
                    href_value = tag.get_attribute('href')
                    link = urljoin(base_url, href_value)
                    print(link)
                    links.append(link)
                    count += 1
                next_page_button_xpath = '//a[@class="pagination__next-link"]'
                next_page_button = wait.until(EC.element_to_be_clickable((By.XPATH, next_page_button_xpath)))
                next_page_button.click()
                page_num +=1
                time.sleep(2)
                
            except Exception as e:
                print(f"Exception: {e}")
                break
        browser.quit()
        links = list(set(links))
        print('Total Count:', len(links))
        self.links = links
        return
    
    def get_articles(self, sleep_time=3):
        print('running get_articles()...')
        results = pd.DataFrame(columns=['title', 'date_published', 'news_outlet', 'authors', 'text'])
        count = 0
        chrome_options = Options()
        chrome_options.add_argument('--headless') 
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 180)

        for l in self.links:
            try:
                print(l)
                browser.get(l)

                # Wait until the page is loaded or raise a TimeoutException
                wait.until(
                    EC.presence_of_element_located((By.XPATH, '/html/head/title'))
                )

                page_html = browser.page_source
                soup = BeautifulSoup(page_html, 'html.parser')

                date_published = None
                meta_tag = soup.find('meta', {'property': 'article:published_time'})
                if meta_tag:
                    date_published = meta_tag['content']
                    date_published = date_published.split('T')[0]
                    
                authors = ""
                meta_tag = soup.find('span', {'class': 'entry-wirepartner__byline'})
                if meta_tag:
                    authors = meta_tag.get_text(strip=True)

                meta_tag = soup.find('meta', {'property': 'og:title'})
                if meta_tag:
                    title = meta_tag['content']

                # Find all <p> tags inside the <div> tag
                content=""
                div_element = soup.find('div', class_='primary-cli cli cli-text')
                for div in div_element:
                    p_element = div.find('p')
                    if p_element:
                        text_content = p_element.get_text(strip=True)
                        content += text_content

                data = {
                    'title': title,
                    'date_published': date_published,
                    'news_outlet': self.newspaper,
                    'authors': authors,
                    'text': content,
                }
                df_dictionary = pd.DataFrame([data])
                results = pd.concat([results, df_dictionary], ignore_index=True)
                print(data['title'])
                print(data['text'])
                print(data['date_published'])
                print(data['authors'])
                print(data['news_outlet'])
                time.sleep(sleep_time)
                count += 1
            
            except TimeoutException as te:
                print(f"TimeoutException")
                break
            except Exception as e:
                print(f"Exception: {e}")
                continue
                
        browser.close()
        print("Count: ", count)
        return results
    
    