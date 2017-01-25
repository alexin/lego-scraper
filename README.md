# lego-scraper
A web scraper for Lego parts.

# Instructions
Requirements:
```
$ pip install -r requirements.txt
```

Scraping:
```
$ python bricklink_scraper.py 9398
```
Scrape multiple models by specifying them one after another:
```
$ python bricklink_scraper.py 9392 8547 9398 42043 42065
```

Results are saved as CSV files, one for each model. If multiple models are specified, then an additional file is created, aggregating all results.

# Sites supported
* [bricklink](www.bricklink.com)

# Notes
The data is currently fit to be imported by Google Spreadsheets.
