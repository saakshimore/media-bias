import streamlit as st 
import plotly.graph_objects as go 
from sqlalchemy import create_engine, text
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import csv
import os
# import threadings
import base64
from io import BytesIO
from wordcloud import WordCloud, STOPWORDS
import requests
from bs4 import BeautifulSoup
  
def load_data():
    # Setup a connection to the database
    conn_string = 'mysql+pymysql://{user}:{password}@{host}/{db}?charset={encoding}'.format(
        host = 'db.ipeirotis.org',
        user = 'student',
        db = 'public',
        password = 'dwdstudent2015',
        encoding = 'utf8mb4')
    engine = create_engine(conn_string)
    with engine.connect() as connection:
        results = connection.execute(text(f'''
        SELECT title, date_published, news_outlet, article_score, confidence_score
        FROM public.bcw_8427_6ec46244'''))
        rows = results.fetchall()
    news_df = pd.DataFrame(rows)
    return news_df


def load_pct_data(news_df):
    news_df['Score_Category'] = pd.cut(
        news_df['article_score'],
        bins=[float('-inf'), -0.001, 0.001, float('inf')],
        labels=['Pro-Israeli', 'Neutral', 'Pro-Palestinian'],  # Include 'Neutral' in the labels
        right=False  # Ensure that 0.0 is included in the 'Neutral' category
    )
    # Group by 'News_Outlet' and 'Score_Category', calculate the percentage, and pivot the result
    percentage_df = news_df.groupby(['news_outlet', 'Score_Category']).size().unstack(fill_value=0)
    percentage_df = percentage_df.div(percentage_df.sum(axis=1), axis=0) * 100
    percentage_df = percentage_df.reset_index()
    return percentage_df

def load_content_data():
    conn_string = 'mysql+pymysql://{user}:{password}@{host}/{db}?charset={encoding}'.format(
        host = 'db.ipeirotis.org',
        user = 'student',
        db = 'public',
        password = 'dwdstudent2015',
        encoding = 'utf8mb4')
    engine = create_engine(conn_string)
    with engine.connect() as connection:
        results = connection.execute(text(f'''
        SELECT title, date_published, news_outlet, content, article_score, confidence_score 
        FROM public.bcw_8427_7e57c245'''))
        rows = results.fetchall()
    content_df = pd.DataFrame(rows)
    return content_df


def update_conflict_data():
    url = "https://acleddata.com/curated-data-files/#regional"
    # Add a user-agent to pretend to be a browser
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    # Send an HTTP GET request to the URL
    response = requests.get(url, headers=headers)

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all the download links
    download_links = soup.find_all('a', class_='download-button')

    # Define a keyword to identify files related to "Middle East"
    keyword = "MiddleEast"

    date_pattern = r'\d{1,2} [A-Za-z]+ \d{4}'
    tags_with_keyword = soup.find_all(lambda tag: tag.name == 'h1' and keyword in tag.get_text())
    if tags_with_keyword:
        h1_tag = tags_with_keyword[0]
        date = h1_tag.get_text()
        match = re.search(date_pattern, date)
        if match:
            date = match.group(0)
            print(date)
        else:
            print("Date not found")
    else:
        print("No <h1> tag with 'MiddleEast' keyword found")
    # Loop through the download links and process the relevant ones
    for link in download_links:
        href = link.get('href')
        file_info = link.find('small').get_text()
        if keyword in file_info:
            print(f"Found relevant file: {file_info}")
            xlsx_response = requests.get(href)
            with open('downloaded_file.xlsx', 'wb') as xlsx_file:
                xlsx_file.write(xlsx_response.content)
            data = pd.read_excel('downloaded_file.xlsx')
            break
    df = data[data['EVENT_ID_CNTY'].str[:3].isin(["PSE", "ISR"])]
    current_directory = os.getcwd()
    parent_directory = os.path.dirname(current_directory)
    data_directory = os.path.join(parent_directory, 'data')
    os.makedirs(data_directory, exist_ok=True)
    csv_path = os.path.join(data_directory, 'acled_data.csv')
    df.to_csv(csv_path, index=False)
    return df        

def get_conflict_plot_data():
    root_dir = os.path.dirname(os.path.abspath(__file__))  # Get the absolute path to the current script (src folder)
    data_path = os.path.join(root_dir, '..', 'data') 
    conflict_data = os.path.join(data_path, 'acled_data.csv')
    if os.path.exists(conflict_data):
        df = pd.read_csv(conflict_data)
    else:
        df = update_conflict_data()
    geojson_path = os.path.join(data_path, 'geojson')
    israel_map_path = os.path.join(geojson_path, 'israel-detailed-boundary.geojson')
    pal_map_path = os.path.join(geojson_path, 'palestine.geojson')
    full_map_path = os.path.join(geojson_path, 'fullmap.geojson')
    israel_map = gpd.GeoDataFrame.from_file(israel_map_path)
    pal_map = gpd.GeoDataFrame.from_file(pal_map_path)
    full_map = gpd.GeoDataFrame.from_file(full_map_path)
    return df, israel_map, pal_map, full_map

st.set_page_config(page_title="Media Bias in Israel-Palestine Coverage", page_icon="📈", layout="wide")


current_directory = os.path.dirname(os.path.realpath(__file__))
css_file_path = os.path.join(current_directory, '..', 'css', 'styles.css')
# Read CSS file
with open(css_file_path, 'r') as css_file:
    custom_css = css_file.read()
# Inject custom CSS
st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)


# Section: Introduction
st.markdown("<h1 style='text-align: center; color: #d30b0d;'>Media Bias in Israel-Palestine</h1>", unsafe_allow_html=True)
st.markdown('''This data product will help users analyze bias in news agencies regarding their coverage of the Israel-Palestine Conflict.''')
news_df = load_data()
percentage_df = load_pct_data(news_df)
bias_mapping = {
    'Vox': 'Left',
    'CNN': 'Center',
    'BBC': 'Center',
    'Wall Street Journal': 'Right',
    'Fox News': 'Right',
    'TheAtlantic': 'Left'
}
news_df['bias'] = news_df['news_outlet'].map(bias_mapping)
counts = pd.DataFrame(news_df['news_outlet'].value_counts().reset_index())
counts.columns = ['news_outlet', 'num']
average_scores = news_df.groupby('news_outlet')['article_score'].mean().reset_index()
summary_df = pd.merge(counts, average_scores, on='news_outlet', how='inner')
summary_df.columns = ['news_outlet', 'num_articles', 'average_score']
summary_df['bias'] = summary_df['news_outlet'].map(bias_mapping)
# Group by news_outlet and count the number of articles for each outlet
outlet_counts = news_df['news_outlet'].value_counts().reset_index()
outlet_counts.columns = ['news_outlet', 'article_count']






st.markdown("<br><br><br><br>", unsafe_allow_html=True)








#Section: Political Bias
st.markdown("<h3 style='text-align: center; color: #013364;', id='distribution'>Sentiment Score and Political Bias</h3>", unsafe_allow_html=True)
scaling_factor = 0.05
x_category_order = ['Right', 'Center', 'Left']
color_discrete_map = {'Left': '#D62828', 'Right': '#003049', 'Center': '#FCBF49'}
fig = px.scatter(
    summary_df,
    x='bias',
    y='average_score',
    size='num_articles',
    size_max=summary_df['num_articles'].max() * scaling_factor,
    text='news_outlet',
    labels={'average_score': 'Average Sentiment Score', 'num_articles': 'Number of Articles', 'bias': 'Bias'},
    # title='Average Sentiment Scores and Number of Articles per News Outlet',
    color='bias',
    color_discrete_map=color_discrete_map,
    height=500
)
text_color = '#000000'  # Specify the desired color using a hexadecimal code
fig.update_traces(textfont=dict(color=text_color))
fig.update_layout(
    xaxis=dict(title='Bias', categoryorder='array', categoryarray=x_category_order),
    yaxis=dict(title='Average Sentiment Score'),
    width=600,  # Adjust the width as needed
    height=500,  # Adjust the height as needed
    margin=dict(l=20, r=20, b=50, t=50)  # Adjust the margins as needed
)
st.plotly_chart(fig, use_container_width=True)




st.markdown("<br><br><br><br>", unsafe_allow_html=True)








#Section: Pie Chart Data distri
st.markdown("<h3 style='text-align: center; color: #013364;', id='distribution'>Data Distribution</h3>", unsafe_allow_html=True)
# color_discrete_map_pie = {
#     'Vox': '#eae2b7',
#     'CNN': '#d62828',
#     'BBC': '#f77f00',
#     'Wall Street Journal': '#fcbf49',
#     'Fox News': '#003049',
#     'TheAtlantic': '#add8e6'
# }
# fig = px.pie(outlet_counts,
#              names='news_outlet',
#              values='article_count',
#              # title='Percentage of Articles That Are from Each News Outlet',
#              hover_data=['article_count'],
#              labels={'article_count': 'Article Count'},
#              color='news_outlet',
#              color_discrete_map=color_discrete_map_pie,
#              template='plotly',
#              width=700, height=700)

# # Display the pie chart in Streamlit
# st.plotly_chart(fig, use_container_width=True)
bin_edges = [-1.05, -0.95, -0.85, -0.75, -0.65, -0.55, -0.45, -0.35, -0.25, -0.15, -0.05,
             0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95, 1.05]

# Create an interactive histogram using Plotly Express
histogram_fig = px.histogram(news_df, 
                             x='article_score', 
                             nbins=len(bin_edges)-1, 
                             range_x=[min(bin_edges), max(bin_edges)], 
                             labels={'article_score': 'Article Score'})
histogram_fig.update_layout(title='Distribution of Article Scores',
                            xaxis_title='Article Score',
                            yaxis_title='Number of Articles',
                            showlegend=True,
                            height=500)

# Create a pie chart
color_discrete_map_pie = {
    'Vox': '#eae2b7',
    'CNN': '#d62828',
    'BBC': '#f77f00',
    'Wall Street Journal': '#fcbf49',
    'Fox News': '#003049',
    'TheAtlantic': '#add8e6'
}
pie_fig = px.pie(outlet_counts,
                 names='news_outlet',
                 values='article_count',
                 hover_data=['article_count'],
                 labels={'article_count': 'Article Count'},
                 color='news_outlet',
                 color_discrete_map=color_discrete_map_pie,
                 template='plotly',
                 title = 'Distribution of News Sources',
                 width=700, height=500)
pie_fig.update_layout(legend=dict(y=0.5))
# Display in two columns
# pie_fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))  # Adjust margin values as needed

# Display in two columns with more space between them
col1, spacer, col2 = st.columns([2, 0.5, 2])  # Adjust width ratios and spacer width as needed

# Display the pie chart in the first column
col1.plotly_chart(pie_fig, use_container_width=True)

# Display the spacer
spacer.text("")

# Display the histogram in the second column
col2.plotly_chart(histogram_fig, use_container_width=True)










st.markdown("<br><br><br><br>", unsafe_allow_html=True)







#Section: List of articles
st.markdown("<h3 style='text-align: center; color: #013364;', id='distribution'>List of Articles</h3>", unsafe_allow_html=True)
df = news_df
df['date_published'] = df['date_published'].dt.date
df = df.drop('confidence_score', axis=1, errors='ignore')
outlet_options = np.append(['All'], df['news_outlet'].unique())
date_range = st.date_input('Select Date Range:', [df['date_published'].min(), df['date_published'].max()])
selected_source = st.selectbox('Select Source:', outlet_options)
score_category = st.selectbox('Select Source:', df['Score_Category'].unique())
k = st.slider('Select Top K Articles:', min_value=1, max_value=50, value=min(10, len(df)))
if selected_source == 'All':
    filtered_df = df
else:
    filtered_df = df[df['news_outlet'] == selected_source]
    
date_range = [np.datetime64(date) for date in date_range]
filtered_df = filtered_df[
    (filtered_df['date_published'] >= date_range[0]) &
    (filtered_df['date_published'] <= date_range[1]) &
    (filtered_df['Score_Category'] == score_category)
]
# Sort and display the top k articles
result_df = filtered_df.sort_values(by='article_score', ascending=False).head(k).reset_index(drop=True)
st.table(result_df)









st.markdown("<br><br><br><br>", unsafe_allow_html=True)








# Section: Percent of Pro-Israeli vs Pro-Palestinian Chart
st.markdown("<h3 style='text-align: center; color: #013364;', id='percent'>Percent of Pro-Israeli vs Pro-Palestinian Articles</h3>", unsafe_allow_html=True)
color_discrete_map = {'Pro-Palestinian': '#D62828', 'Pro-Israeli': '#003049', 'Neutral':'#EAE2B7'}
fig = px.bar(
    percentage_df,
    x='news_outlet',
    y=['Pro-Israeli','Neutral', 'Pro-Palestinian'],
    labels={'value': 'Percentage', 'variable': 'Score Category'},
    color_discrete_map=color_discrete_map,
    # title='Percentage of Articles Pro-Israeli Articles by News Outlet',
    # color='variable',
    height=700
)
fig.update_layout(
    yaxis=dict(title='Percentage'),
    xaxis=dict(title='News Outlet'),
    barmode='stack',
    width=600,  # Adjust the width as needed
    height=500,  # Adjust the height as needed
    margin=dict(l=20, r=20, b=50, t=50),
)
st.plotly_chart(fig, use_container_width=True)







st.markdown("<br><br><br><br>", unsafe_allow_html=True)




#Section: Distribution
st.markdown("<h3 style='text-align: center; color: #013364;', id='distribution'>Number of Articles related to Israel & Palestine per News Outlet per Week</h3>", unsafe_allow_html=True)
news_df['date_published'] = pd.to_datetime(news_df['date_published'], errors='coerce')
news_df = news_df.dropna(subset=['date_published'])
news_df = news_df[news_df['date_published'] >= '2023-09-01']
news_df['Week'] = news_df['date_published'].dt.strftime('%Y-%U')
articles_per_week = news_df.groupby(['Week', 'news_outlet']).size().unstack(fill_value=0)
articles_per_week_long = articles_per_week.reset_index().melt(id_vars='Week', 
                                                              var_name='News_Outlet', 
                                                              value_name='Number_of_Articles')
week_start_dates = pd.to_datetime(articles_per_week.index.str.split('-').str[0] 
                                  + '-W' 
                                  + articles_per_week.index.str.split('-').str[1] 
                                  + '-1', format='%Y-W%U-%w')
week_start_dates = week_start_dates.strftime('%Y-%m-%d')
color_discrete_map = {
    'Vox': '#eae2b7',
    'CNN': '#d62828',
    'BBC': '#f77f00',
    'Wall Street Journal': '#fcbf49',
    'Fox News': '#003049',
    'TheAtlantic': '#add8e6'
}
fig = px.bar(
    articles_per_week_long,
    x='Week',
    y='Number_of_Articles',
    color='News_Outlet',
    labels={'Number_of_Articles': 'Number of Articles', 'Week': 'Week Start Date'},
    # title='Number of Articles related to Israel & Palestine per News Outlet per Week'
    color_discrete_map=color_discrete_map
)

# Configure the layout
fig.update_layout(
    xaxis=dict(title='Weeks from Oct 7, 2023', tickangle=45),
    yaxis=dict(title='Number of Articles'),
    legend_title='News Outlet'
)

# Show the Plotly chart
st.plotly_chart(fig, use_container_width=True)




st.markdown("<br><br><br><br>", unsafe_allow_html=True)




#Section: Pro-Palestinian Sentiment over Time
st.markdown("<h3 style='text-align: center; color: #013364;', id='distribution'>Sentiment over Time</h3>", unsafe_allow_html=True)
# st.markdown('''This graph looks at the percentage of pro-Palestinian articles released by the agency over time.''')

# Assuming 'date_published' is in datetime format
news_df['date_published'] = pd.to_datetime(news_df['date_published'], errors='coerce')
# Drop rows with NaT (invalid dates)
news_df = news_df.dropna(subset=['date_published'])
# Set the reference date
reference_date = pd.to_datetime('2023-10-07')
# Filter dates greater than or equal to the reference date
news_df['Week'] = np.where(news_df['date_published'] < reference_date,
                                  -1 * (reference_date - news_df['date_published']).dt.days // 7,
                                  (news_df['date_published'] - reference_date).dt.days // 7 + 1)

avg_scores = news_df.groupby(['news_outlet', 'Week'])['article_score'].mean().reset_index()
color_discrete_map = {
    'Vox': '#eae2b7',
    'CNN': '#d62828',
    'BBC': '#f77f00',
    'Wall Street Journal': '#fcbf49',
    'Fox News': '#003049',
    'TheAtlantic': '#add8e6'
}
fig = px.line(avg_scores, 
              x='Week', 
              y='article_score', 
              color='news_outlet',
              color_discrete_map=color_discrete_map, 
              labels={'article_score': 'Average Article Score', 'variable': 'News Outlet'})
fig.update_layout(title='Average Sentiment Score over Time',
    xaxis_title='Weeks from Oct 7, 2023',
    yaxis_title='Average Article Score',
    legend_title='News Outlet'
                 )
st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Bin the scores
news_df['Score_Category'] = pd.cut(news_df['article_score'], bins=[float('-inf'), 0, float('inf')], labels=['Negative', 'Positive'])
# Group by 'Week', 'News_Outlet', and 'Score_Category', calculate the percentage, and pivot the result
percentage_positive_articles = (
    news_df[news_df['Score_Category'] == 'Positive']
    .groupby(['Week', 'news_outlet'])
    .size()
    .div(news_df.groupby(['Week', 'news_outlet']).size())
    .mul(100)
    .unstack(fill_value=0)
)
# Group by 'Week' and 'News_Outlet', and count the number of articles
articles_per_week = news_df.groupby(['Week', 'news_outlet']).size().unstack(fill_value=0)

fig = px.line(
    percentage_positive_articles.reset_index(),
    x='Week',
    y=percentage_positive_articles.columns,
    labels={'value': 'Percentage', 'variable': 'News Outlet'},
    # title='Percentage of Pro-Palestinian Articles per News Outlet per Week',
    color_discrete_map=color_discrete_map,
)
fig.update_layout(
    title = 'Pro-Palestinian Sentiment over Time',
    xaxis=dict(title='Weeks from Oct 7, 2023'),
    yaxis=dict(title='Percentage'),
    legend_title='News Outlet'
)
st.plotly_chart(fig, use_container_width=True)







st.markdown("<br><br><br><br>", unsafe_allow_html=True)








#Section:  Word Frequency
st.markdown("<h3 style='text-align: center; color: #013364;', id='distribution'>Word frequency</h3>", unsafe_allow_html=True)
df = load_content_data()
df['date_published'] = pd.to_datetime(df['date_published'])
filtered_df = df[df['date_published'] >= '2023-09-01']
filtered_df['date_published'] = filtered_df['date_published'].dt.date
default_start_date = filtered_df['date_published'].min()
default_end_date = filtered_df['date_published'].max()
# date_range = st.date_input('Select Date Range:', [default_start_date, default_end_date])
# # User-selectable Date Range
start_date = st.date_input('Start Date', min_value=default_start_date, max_value=default_end_date, value=default_start_date)
end_date = st.date_input('End Date', min_value=default_start_date, max_value=default_end_date, value=default_end_date)
# User-inputted Keyword Search
keyword = st.text_input('Enter Keyword for Count:', 'Hamas')
# Multi-Selection for News Outlets
selected_outlets = st.multiselect('Select News Outlets:', filtered_df['news_outlet'].unique(), default=filtered_df['news_outlet'].unique())
# Filter DataFrame based on user inputs
# start_date = pd.to_datetime(start_date)
# end_date = pd.to_datetime(end_date)
filtered_df = filtered_df[(filtered_df['date_published'] >= start_date) & (filtered_df['date_published'] <= end_date)]
filtered_df['mention_count'] = filtered_df['content'].str.count(keyword)
filtered_df = filtered_df[filtered_df['news_outlet'].isin(selected_outlets)]
# filtered_df['mention_count'] = filtered_df['content'].str.count('Hamas')
average_mentions_per_outlet_over_time = filtered_df.groupby(['news_outlet', filtered_df['date_published']])['mention_count'].mean()
average_mentions_per_outlet_over_time = average_mentions_per_outlet_over_time.unstack(level='news_outlet')
average_mentions_per_outlet_over_time = average_mentions_per_outlet_over_time.reset_index()
melted_df = pd.melt(average_mentions_per_outlet_over_time, id_vars='date_published', var_name='news_outlet', value_name='mention_count')
color_discrete_map = {
    'Vox': '#eae2b7',
    'CNN': '#d62828',
    'BBC': '#f77f00',
    'Wall Street Journal': '#fcbf49',
    'Fox News': '#003049',
    'TheAtlantic': '#add8e6'
}
fig = px.line(melted_df,
              x='date_published',
              y='mention_count',
              color='news_outlet',
              color_discrete_map=color_discrete_map,
              labels={'mention_count': 'Average Mentions per Article'},
              title=f'Frequency of "{keyword}" per Article over Time',
              markers=True,
              width=800,
              height=500)
fig.update_layout(
    xaxis_title='Date Published',
    yaxis_title='Frequency',
    legend_title='News Outlet'
    )
st.plotly_chart(fig, use_container_width=True)
result_df = filtered_df.drop(['content','confidence_score'], axis=1, errors='ignore').sort_values(by='mention_count', ascending=False).head(10).reset_index(drop=True)
st.table(result_df)









st.markdown("<br><br><br><br>", unsafe_allow_html=True)







#Section:  Word Cloud generator
st.markdown("<h3 style='text-align: center; color: #013364;', id='distribution'>Word Cloud Generator</h3>", unsafe_allow_html=True)
df = load_content_data()
selected_outlets = st.multiselect('Select News Outlets:', df['news_outlet'].unique(), default=df['news_outlet'].unique())
wordcloud_df = df[df['news_outlet'].isin(selected_outlets)]
text_content = ' '.join(wordcloud_df['content'].dropna())
stop_words = set(STOPWORDS)
stop_words.add('Israel')
stop_words.add('Gaza')
stop_words.add('said')
stop_words.add('s')
stop_words.add('u')
wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stop_words).generate(text_content)
fig, ax = plt.subplots(figsize=(6, 4))
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis('off')
# ax.set_title('Word Cloud of Content')
st.pyplot(fig)












st.markdown("<br><br><br><br>", unsafe_allow_html=True)







#Section:  Conflict data heatmap
st.sidebar.markdown("<h3 style='text-align: center; color: #013364;', id='distribution'>On-Ground Reality</h3>", unsafe_allow_html=True)

update_button_clicked = st.sidebar.button('Get Latest Conflict Data', key='update_button', help="Note: Updating will take time.")
if update_button_clicked:
    temp = update_conflict_data()
    st.sidebar.markdown("<p style='color: lightgrey; font-size: small;'>Data updated successfully!</p>", unsafe_allow_html=True)

st.sidebar.markdown("""
    <style>
        #update_button {
            background-color: #4CAF50;
            color: white;
            text-align: center;
            width: 100%;
            padding: 8px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
""", unsafe_allow_html=True)

# Get conflict plot data
df, israel_map, pal_map, full_map = get_conflict_plot_data()
df.columns = df.columns.str.lower()
df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')

# Date range input in the sidebar
start_date = st.sidebar.date_input('Start Date', df['event_date'].min())
end_date = st.sidebar.date_input('End Date', df['event_date'].max())
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filter data based on date range
filtered_df = df[(df['event_date'] >= start_date) & (df['event_date'] <= end_date)]
filtered_df = filtered_df[filtered_df['longitude'].between(filtered_df['longitude'].quantile(0.1), filtered_df['longitude'].quantile(0.99))]
filtered_df = filtered_df[filtered_df['longitude'] > 33.5]

last_updated_date = df['event_date'].max().strftime('%Y-%m-%d')
st.sidebar.markdown(f"<p style='color: lightgrey; font-size: small;'>Last Updated: {last_updated_date}</p>", unsafe_allow_html=True)

fig, ax = plt.subplots(figsize=(6, 6))
full_map.plot(ax=ax, linewidth=1, color='White', edgecolor='Black', alpha=1)
sns.kdeplot(
    data=filtered_df,
    x='longitude',
    y='latitude',
    shade=True,
    cmap='rainbow',
    alpha=0.5,
    n_levels=20,
    ax=ax,
    gridsize=100
)

scatter = filtered_df.plot(
    kind='scatter',
    x='longitude',
    y='latitude',
    ax=ax,
    s=0.01,
    alpha=0.5
)

plt.title('KDE for armed conflicts in Israel and Palestine')
plt.xlabel('Longitude')
plt.ylabel('Latitude')

# Display the plot in the sidebar
st.sidebar.pyplot(fig)
