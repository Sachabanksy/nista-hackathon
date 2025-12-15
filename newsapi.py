import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import boto3
import json

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='eu-west-2' 
)

apiKey = '3a8ed99c2788406597f10863425befc4'

# Define multiple query terms
queries = ['Sizewell C', 'High Speed 2', 'AUKUS']

# List to store all dataframes
all_dfs = []

# Iterate through each query
for query in queries:
    print(f"Fetching articles for: {query}")
    
    # API URL
    url = f"https://newsapi.org/v2/everything?q={query}&language=en&from=2025-11-12&sortBy=popularity&apiKey={apiKey}"
    
    # Fetch the data
    response = requests.get(url)
    data = response.json()
    
    # Convert articles to DataFrame
    if data['articles']:
        query_df = pd.DataFrame(data['articles'])
        # Add a column to track which query returned this article
        query_df['search_query'] = query
        all_dfs.append(query_df)
    else:
        print(f"No articles found")

# Combine all dataframes
if all_dfs:
    df = pd.concat(all_dfs, ignore_index=True)
    
    # Remove duplicate articles (same URL)
    df_unique = df.drop_duplicates(subset='url', keep='first')
else:
    print("No articles found for any query")
    df_unique = pd.DataFrame()


# Function to scrape content from a URL
def scrape_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        return text
    
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None
    
def generate_summary(content):
    if not content or content.strip() == '':
        return None
    
    try:
        # Truncate content if too long (Claude has token limits)
        max_chars = 15000
        truncated_content = content[:max_chars] if len(content) > max_chars else content
        
        # Prepare the prompt - more direct instruction
        prompt = f"Summarize the following article in exactly 100 words. Provide only the summary without any preamble:\n\n{truncated_content}"
        
        # Prepare request body for Claude 3 Sonnet
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        # Call Bedrock
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=body
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        summary = response_body['content'][0]['text'].strip()
        
        # Check if summary exists before processing
        if not summary:
            return None
        
        # Remove common prefixes if they exist
        prefixes_to_remove = [
            "Here is a 100 word summary:",
            "Here is a 100-word summary:",
            "Here's a 100 word summary:",
            "Here's a 100-word summary:",
            "Here is the summary:",
            "Here's the summary:",
            "Here is a 100-word summary of the article:"
        ]
        
        for prefix in prefixes_to_remove:
            if summary.lower().startswith(prefix.lower()):
                summary = summary[len(prefix):].strip()
                break
        
        return summary
    
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        return None

# Create lists to store results
urls = []
headlines = []
contents = []

# Iterate through each URL and scrape content
for idx, row in df.iterrows():
    article_url = row['url']
    headline = row['title']
    print(f"Scraping {idx + 1}/{len(df)}: {article_url}")
    
    content = scrape_content(article_url)
    
    urls.append(article_url)
    contents.append(content)
    headlines.append(headline)
    
    time.sleep(1)

# Create new DataFrame with scraped content
scraped_df = pd.DataFrame({
    'url': urls,
    'content': contents,
    'headline': headlines
})

print(scraped_df.head())

scraped_df.to_excel('scraped_newsapi.xlsx')

summaries = []
for idx, row in scraped_df.iterrows():
    print(f"Summarizing article {idx + 1}/{len(scraped_df)}")
    summary = generate_summary(row['content'])
    summaries.append(summary)
    time.sleep(0.5)  # Small delay to avoid rate limits


# Add summaries column to dataframe
scraped_df['summary'] = summaries

scraped_df.to_excel('scraped_data_summaries.xlsx')