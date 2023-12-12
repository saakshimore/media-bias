# Media Bias in the Coverage of Israel and Palestine
## Problem Statement: Visualize the bias in media regarding the coverage of Israel and Palestine

View the project website live on [streamlit](https://media-bias-israel-palestine.streamlit.app/) (please switch to light theme for better readability).

The goal of our project is to analyze the bias of various news sources on the Israeli-Palestinian conflict. We chose this topic since it is one of the biggest events of this year, and it is important to understand news sources’ bias so we can account for it when we read them. We scraped the title, date published, news outlet, authors, and text from articles with the keywords “Gaza”, “Hamas”, “Israel”, and “Palestine” from The Atlantic, Vox, BBC, CNN, Fox News, and The Wall Street Journal. We chose these sources since they are popular, have different viewpoints, and are the easiest to scrape. The earliest date published differs based on the capabilities of our scraper for each source, but our timeframe for each source starts before the war. We asked the OpenAI API to use the title, text, and its knowledge of the political bias of the source to give each article an article score from -1 to 1 in 0.1 intervals, with -1 being the most pro-Israeli, and 1 being the most pro-Palestinian. We also used the API to assign each article a confidence score from 0 to 1 in 0.1 intervals, representing the API’s confidence in the accuracy of its article score. We also used data from an ACLED database to create a KDE of events related to the Israeli-Palestinian conflict to contrast where the news focuses on, and where the conflict impacts people the most. 

## Methodology:
1. Scrape news articles using Selenium and BeautifulSoup:
    * Sources: Fox News, Wall Street Journal (account required), BBC, CNN, the Atlantic, Vox
    * Keywords: Palestine, Israel, Hamas, Gaza
    * Date Range: From Oct 2023 (in most cases) to current date
    
2. Sentiment Score Calculation:
    * Do prompt engineering via OpenAI's API to get a sentiment score for each article where sentiment is defined between -1 and 1, where -1 is strongly pro-Israeli, 1 is strongly pro-Palestine (maximum possible), and 0 is neutral. 
    * Upload the data to MySQL Workbench
    
3. Website
    * Data Analysis and Visualization via Streamlit
    
    
4. Additional Data
    * Have a simultaneous heatmap for live conflict data in Palestine and Israel (ACLED Data)

## Data Collected:
* We were able to collect over 2k articles via scraping
* The distribution of data was skewed solely because of scraping abilities. The count is given below:

| News Outlet          | Count |
|----------------------|-------|
| CNN                  | 852   |
| TheAtlantic          | 389   |
| Fox News             | 303   |
| Vox                  | 184   |
| Wall Street Journal  | 180   |
| BBC                  | 118   |



## Results:
| News Outlet          | Article Score |
|----------------------|---------------|
| BBC                  | 0.083051      |
| CNN                  | 0.081338      |
| Fox News             | -0.125083     |
| TheAtlantic          | 0.013368      |
| Vox                  | 0.045109      |
| Wall Street Journal  | -0.070000     |

* We observed that right-wing news sources (bias defined by [this](https://www.allsides.com/media-bias) chart) tend to be more pro-Israeli than center or left-wing sources.
* Center-wing news agencies are most pro-Palestinian than left-wing sources, which is counter-intuitive. However, since our claims are not backed by hypothesis testing, we can attribute this to the skewedness of the data distribution.
* Through word modeling, we discovered that right-wing sources have used the word 'Hamas' a lot more than the other sources, even through the latest events of the war, indicating how they are focusing on that aspect of the war. 
* Please visit the website for all other conclusions and visualizations. 


## Future Work:
A few natural next steps for this project would be to:
* introduce a live feed component for the news scraping
* add more news sources
* make the distribution of data uniform across all sources
* run significance tests on results
* brainstorm how the conflict data can seamlessly be integrated with the media bias problem statement. 


## User Guide

Navigate to the directory where you have cloned the repo. 
```
pip install -r requirement.txt
```
```
python3 src/RunScrapers.py
```
```
python3 src/news_openai.py
```
```
python3 src/mysql_upload.py
```
```
streamlit run src/streamlit.py
```



## Notes:
* The project can be extended to other news sources, given one's scraping abilities. [This](https://github.com/the-dataface/Newspaper-Scrapers) repo was used for inspiration - the code is outdated and incompatible with the current structure of most news websites but it can be tweaked to present day. 
* You must use your own OpenAI key. You should have an upgraded plan to make sure that the tokens are handled properly.
* For additonal concerns and queries, please reach out to these emails: saakshi.more@nyu.edu, bcw8427@nyu.edu, erp9299@nyu.edu. 


