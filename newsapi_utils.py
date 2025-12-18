from bs4 import BeautifulSoup
import boto3
import requests
import pandas as pd
import json


def scrape_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text(separator=" ", strip=True)
        return text

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return None


def get_bedrock_client():
    # read in credentials, this needs to be stored locally
    credentials = pd.read_csv("aws_logins.csv")

    credentials = credentials.set_index("variable_name")

    bedrock = boto3.client(
        service_name="bedrock-runtime",
        aws_access_key_id=credentials.loc["access_key", "variable_value"],
        aws_secret_access_key=credentials.loc["secret_key", "variable_value"],
        region_name="eu-west-2",
    )
    return bedrock


bedrock = get_bedrock_client()


def generate_summary(content):
    if not content or content.strip() == "":
        return None

    max_chars = 15000
    truncated_content = content[:max_chars] if len(content) > max_chars else content

    prompt = f"Summarize the following article in exactly 100 words. Provide only the summary without any preamble:\n\n{truncated_content}"

    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}],
        }
    )

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0", body=body
    )

    response_body = json.loads(response["body"].read())
    summary = response_body["content"][0]["text"].strip()

    # check if summary exists before processing
    if not summary:
        return None

    # Remove annoying prefixes
    prefixes_to_remove = [
        "Here is a 100 word summary:",
        "Here is a 100-word summary:",
        "Here's a 100 word summary:",
        "Here's a 100-word summary:",
        "Here is the summary:",
        "Here's the summary:",
        "Here is a 100-word summary of the article:",
    ]

    for prefix in prefixes_to_remove:
        if summary.lower().startswith(prefix.lower()):
            summary = summary[len(prefix) :].strip()
            break

    return summary
