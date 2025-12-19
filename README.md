# NISTA_Hackathon_Dec_25
repo for dec festive hackathon 

## Hansard Hansard Parliamentary Debate Data

1. Download the data for the years you want, e.g.
```
cd hansard
rsync -az --progress --exclude '.svn' --exclude 'tmp/' --relative data.theyworkforyou.com::parldata/scrapedxml/debates/debates2024-*
rsync -az --progress --exclude '.svn' --exclude 'tmp/' --relative data.theyworkforyou.com::parldata/scrapedxml/debates/debates2025-* 
```
2. Run the code to make the dataframe
```
python read_hansard_files.py
```
## News API Scraping

This script uses the News API to search for news articles relating to specific search terms i.e project names. It then returns urls relating to these news articles and using beautiful soup, scrapes the html content of the website and does some light cleaning.
The script then hooks up to AWS Bedrock to generate summaries of the textual content and returns a dataframe of the headline, content, and summary.

In order to run this script you will need a .env file with an apiKey stored inside it, and a credentials.csv file which has the aws credentials necessary to hook up to bedrock. Ask Jack for both of these :)

## Google Trends

The google trends script uses the unofficial Google Analytics API Python Package (pytrends). You can just pip install this in your virtual environment, and go from there. The amount you can use the package is fairly limited, as it is a free package, so feel free to explore other ways of using google analytics data - or split up the running of the package within your team to maximise use.
