# DataCollectionSAT

After cloning the repo, do:

pip install scrapy

cd newegg_com/

scrapy crawl newegg -o test500.csv

Scraper scrapes all products but stops at 500 products, to scrape more edit self.max_products.
Scraper currently scrapes all products from the Health-Sports category.
To scrape another or more categories, uncomment the other categories at line 38.

This is the first version, after adding pagination scraping, this crawler will be able to scrape the whole website.