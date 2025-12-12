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
