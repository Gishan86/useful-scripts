# Web Scraping
These scripts are used to get data from popular websites.
Either to simply make gathering of data easier or to watch for changes in availability or prices.
They are not meant to build a botnet to buy stuff in bulk that you can then scalp people on though.

Here is an overview:

 - [Amazon Price Scraper](#amazon-price-scraper)

## Amazon Price Scraper
This little script was built because my wife buys cat food from Amazon.
Unfortunately their website design makes it hard to compare prices between different options for an article. So I wrote this script for her which gets all options prices and writes them into a simple CSV file. This way she can simply open that file and see which options are cheapest right now.

[Link](scrape_amazon_prices.py)

### Requirements
 - Python 3
 - BeautifulSoup4 (4.11.2)
 - GetUserAgent (0.0.7)
 - Requests (2.28.2)

### Usage
```
> python scrape_amazon_prices.py -u <BASE-URL> -a <ARTICLE IDs> -g <GROUPS> -o <CSVOUTPUT> -we -uh
```

### Options
```
 -h, --help				Help for all options
 -u URL, --url URL			Base Url of site to be crawled
 -a, --articles ARTICLES [ARTICLES ...]	Ids of articles (can be one or multiple separated by space)
 -g, --groups GROUPS [GROUPS ...]	Optional: To group multiple articles and categorize them
 -o, --output OUTPUT			Path the CSV file gets written to
 -we, --writeempty			Write the CSV file even if nothing was found (default: True)
 -uh, --useheader			Use a random HTTP header for scraping (default: True)
 -v, --verbose				Verbose output for debugging (default: False)
```

### Example
Get prices for all flavours of cat food in 200g and 100g:
```
> python scrape_amazon_prices.py -u https://www.amazon.de/dp/ -a B08MLZQPR9 B07D4T5NR4 -g "200g" "125g" -o "c:\\users\\dev\\desktop\\output.csv" -we -uh
```

Output (CSV content):
The first line contains the time and date the CSV was written.

| **Group** | **Article** | **Price** | **Availability** | **Url** |
| - | - | - | - | - |
| 200g | Turkey | 8.76 | x | https://www.amazon.de/dp/B087MLLVJ5?th=1 |
|  | Chicken | 9.19 | x | https://www.amazon.de/dp/B07D4VMPZT?th=1 |
|  | Beef | 0.00 |  | https://www.amazon.de/dp/B07D4S7PXJ?th=1 |
| 125g | Chicken | 5.49 | x | https://www.amazon.de/dp/B07D4TBKRZ?th=1 |
|  | Turkey | 0.00 |  | https://www.amazon.de/dp/B087MLQ81R?th=1 |
