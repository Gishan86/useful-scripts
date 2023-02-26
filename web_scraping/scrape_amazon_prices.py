import requests
import argparse
from bs4 import BeautifulSoup
from getuseragent import UserAgent
from operator import itemgetter
from os.path import exists
from os import remove
from datetime import datetime
import logging
from itertools import cycle

userAgent = UserAgent("chrome")
HEADER = {"User-Agent": userAgent.Random(), "Accept-Language": "en-US, en;q=0.5"}

def parse_args():
    """Parses arguments and returns their values"""
    argparser = argparse.ArgumentParser(description="Scrapes Amazon for prices of multiple articles and writes them to a csv file.")
    argparser.add_argument("-u", "--url", dest="url", help="Base url of site to be crawled", default="https://www.amazon.de/dp/", required=True)
    argparser.add_argument("-a", "--articles", dest="articles", nargs="+", help="Ids of articles to be scraped", default=[], required=True)
    argparser.add_argument("-g", "--groups", dest="groups", nargs="+", help="Group for each given article", default=[])
    argparser.add_argument("-o", "--output", dest="output", help="Path where the prices will be written (CSV)", default="", required=True)
    argparser.add_argument("-we", "--writeempty", dest="writeempty", help="Writes the csv file even if nothing was found", action=argparse.BooleanOptionalAction, default=True)
    argparser.add_argument("-uh", "--useheader", dest="useheader", help="Use random HTTP header for scraping", action=argparse.BooleanOptionalAction, default=True)
    argparser.add_argument("-v", "--verbose", dest="verbose", help="Verbose output for debugging", action=argparse.BooleanOptionalAction, default=False)
    args = argparser.parse_args()
    return args.url, args.articles, args.groups, args.output, args.writeempty, args.useheader, args.verbose

def get_options(url: str, useheaders: bool):
    """Scrapes the given url to get all options for this article"""
    if useheaders:
        page = requests.get(url, headers=HEADER)
    else:
        page = requests.get(url)

    soup = BeautifulSoup(page.content, "lxml")

    options = []
    try:
        container = soup.find("div", {"id": "tp-inline-twister-dim-values-container"})
        if not container is None:
            #variant-1
            for li in container.findAll("li", "swatch-list-item-text"):
                if "swatch-prototype" in li.attrs["class"]:
                    continue

                url = li["data-asin"]
                if not url:
                    continue

                title = li.find("span", "swatch-title-text").text.strip()
                options.append([url, title])
        else:
            #variant-2
            container = soup.find("div", {"id": "variation_color_name"})

            if container is None:
                return options

            for li in container.find_all("li"):
                url = li["data-defaultasin"]
                if not url:
                    continue

                title = li.find("img")["alt"]
                options.append([url, title])
            
    except:
        pass

    return options

def get_price(url: str, useheaders: bool):
    """Scrapes the given url for the article's price"""
    if useheaders:
        page = requests.get(url, headers=HEADER)
    else:
        page = requests.get(url)
    
    soup = BeautifulSoup(page.content, "lxml")

    price = 0.0
    try:
        span_pricegroup = soup.find("span", attrs={"class": "a-price"})
        span_price = span_pricegroup.find("span", "a-offscreen")
        price = float(span_price.text.replace(",", ".").replace("€", ""))
    except:
        price = 0.0

    #check availability
    avail = soup.find("input", attrs={"id": "add-to-cart-button"}) != None

    if avail == False:
        price = 0.0 #set price to zero, if not available
    
    return price, avail

def scrape(url_base: str, articles: list[str], groups: list[str], useheaders: bool):
    """Scrapes and puts everything in the result list"""
    results = []

    if len(groups) == 0:
        groups = [""]

    articles_grouped = list(zip(articles, cycle(groups)))

    for artId, group in articles_grouped:
        url = url_base + artId

        logging.debug("Scraping article '%s' at '%s'" %(artId, url))

        #get options
        options = get_options(url, useheaders)

        #get price and title for each option
        for opt in options:
            url = url_base + opt[0]
            title = opt[1]

            price, avail = get_price(url, useheaders)
            results.append({"group": group, "title": title, "price": price, "avail": avail, "url": url})
    
    return results

def write(results: list, output: str, writeempty: bool):
    """Writes the result to a csv file"""
    if (writeempty == False) and (results is None or len(results) == 0):
        logging.error("No prices found!")
        return

    #override csv file
    if exists(output):
        remove(output)

    #sort results
    results_sorted = sorted(results, key=itemgetter("group", "price"), reverse=True)

    #write csv file
    with open(output, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M") + "\n")

        f.write("Group;Article;Price;Availability;Url\n")

        if len(results_sorted) == 0:
            f.write("No articles found!")

        last_group = None
        for r in results_sorted:
            availStr = "x"
            if r["avail"] == False:
                availStr = ""
            
            if last_group != r["group"]:
                f.write(r["group"] + "\n")
                last_group = r["group"]
                
            f.write(";" + r["title"] + ";" + str(r["price"]).replace(".", ",") + ";" + availStr + ";" + r["url"] + "\n")

def main():
    #parse arguments
    url, articles, groups, output, writeempty, useheaders, verbose = parse_args()

    #init logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    #scrape prices for all articles
    results = scrape(url, articles, groups, useheaders)

    #write results to csv file
    write(results, output, writeempty)

if __name__ == "__main__":
    main()