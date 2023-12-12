import pandas as pd
import requests
import uuid
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy import text

conn_string = "mysql+pymysql://{user}:{password}@{host}/".format(
    host="db.ipeirotis.org", user="student", password="dwdstudent2015"
)

engine = create_engine(conn_string)
db_name = "public"
create_db_query = (
    f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET 'utf8'"
)

# Create a database
with engine.connect() as connection:
    connection.execute(text(create_db_query))

if "suffix" not in globals():
    suffix = str(uuid.uuid4())[:8]

table_name = f"bcw_8427_{suffix}"
drop_table_query = f"DROP TABLE IF EXISTS {db_name}.{table_name}"
with engine.connect() as connection:
    connection.execute(text(drop_table_query))

create_table_query = f"""CREATE TABLE IF NOT EXISTS {db_name}.{table_name}
                                (title varchar(255),
                                date_published datetime,
                                news_outlet varchar(255),
                                content text,
                                article_score float,
                                confidence_score float,
                                PRIMARY KEY(title)
                                )"""
with engine.connect() as connection:
    connection.execute(text(create_table_query))
query_template = f"""
                    INSERT IGNORE INTO
                    {db_name}.{table_name}(title, date_published, news_outlet, content, article_score, confidence_score)
                    VALUES (:title, :date_published, :news_outlet, :content, :article_score, :confidence_score)
                  """
with engine.connect() as connection:
    for index, entry in combined_df.iterrows():
        query_parameters = {
            "title": entry["title"],
            "date_published": entry["date_published"],
            "news_outlet": entry["news_outlet"],
            "content": entry["content"],
            "article_score": entry["article_score"],
            "confidence_score": entry["confidence_score"]
        }
        connection.execute(text(query_template), query_parameters)
    connection.commit()
    





