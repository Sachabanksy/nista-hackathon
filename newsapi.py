import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import boto3
import json
import os
from dotenv import load_dotenv
from newsapi_utils import scrape_content, get_bedrock_client, generate_summary

load_dotenv()

apiKey = os.getenv("apiKey")

queries = ["Sizewell C", "High Speed 2", "New Hospitals Programme"]

all_dfs = []

# Iterate through each query
for query in queries:
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&from=2025-11-25&sortBy=popularity&apiKey={apiKey}"

    response = requests.get(url)
    data = response.json()

    if data["articles"]:
        query_df = pd.DataFrame(data["articles"])
        query_df["search_query"] = query
        all_dfs.append(query_df)
    else:
        print(f"No articles found")

# combine all dataframes
if all_dfs:
    df = pd.concat(all_dfs, ignore_index=True)
    df_unique = df.drop_duplicates(subset="url", keep="first")
else:
    print("No articles found for any query")
    df_unique = pd.DataFrame()


urls = []
headlines = []
contents = []

# Iterate through each URL and scrape content
for idx, row in df.iterrows():
    article_url = row["url"]
    headline = row["title"]
    print(f"Scraping {idx + 1}/{len(df)}: {article_url}")

    content = scrape_content(article_url)

    urls.append(article_url)
    contents.append(content)
    headlines.append(headline)

    time.sleep(1)

# create dataframe with content
scraped_df = pd.DataFrame({"url": urls, "content": contents, "headline": headlines})


summaries = []
for idx, row in scraped_df.iterrows():
    print(f"Summarizing article {idx + 1}/{len(scraped_df)}")
    summary = generate_summary(row["content"])
    summaries.append(summary)

scraped_df["summary"] = summaries

scraped_df.to_excel("scraped_data_summaries.xlsx")
