import logging

import scrapy
from scrapy.exceptions import CloseSpider

from scrapy.loader import ItemLoader
from ..items import NeweggComItem

class NeweggSpider(scrapy.Spider):
    name = 'newegg'
    allowed_domains = ['newegg.com']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parsed_product_ids = set()
        self.max_products = 500
        self.PER_PAGE = 36

    def _generate_maincategory_request(self, category):
        url = 'https://www.newegg.com/' + str(category)
        return scrapy.Request(url, callback=self.parse_categories, meta={'main_category': category})

    def _generate_subcat_request(self, subcat_url):
        return scrapy.Request(url=subcat_url, callback=self.parse_categories, meta={'subcat_url': subcat_url})

    def _generate_page_request(self, url, curr_page, total_pages):
        return scrapy.Request(url=url, callback=self.parse_list_products, meta={'curr_page': curr_page, 'total_pages': total_pages})

    def _generate_product_request(self, product_url):
        return scrapy.Request(url=product_url, callback=self.parse_product)

    # Start
    def start_requests(self):
        """
        Scraping only 1 category fully, to scrape all we need rotating proxies in order to not get blocked
        or we let the scraper run for 24 hours (a long time)
        """
        categories = {
            # 'Components-Storage/Store/ID-1',
            # 'Computer-Systems/Store/ID-3',
            # 'Computer-Peripherals/Store/ID-380',
            # 'Appliances/Store/ID-13',
            # 'TV-Home-Theater/Store/ID-16',
            # 'Electronics/Store/ID-10',
            # 'Gaming-VR/Store/ID-8',
            # 'Networking/Store/ID-889',
            # 'Smart-Home-Security/Store/ID-2',
            # 'Office-Solutions/Store/ID-133',
            # 'Software-Services/Store/ID-6',
            # 'Automotive-Tools/Store/ID-192',
            # 'Home-Outdoors/Store/ID-15',
            'Health-Sports/Store/ID-78',
            # 'Toys-Drones-Maker/Store/ID-266',
        }

        requests = []

        logging.info('Process all main categories')
        for cat in categories:
            requests.append(self._generate_maincategory_request(cat))

        return requests

    # Parse all the subcategories of every category
    def parse_categories(self, response):
        subcats = response.css('a.filter-box-label::attr(href)').extract()
        # filtered_subcats = [s for s in subcats if "Category" in s]
        logging.info(subcats)
        requests = []

        def add_https(url):
            # Checks if a URL has the 'https:' scheme, and adds it if it's missing.
            if not url.startswith('https:'):
                url = 'https:' + url
            return url

        if subcats:
            for subcat in subcats:
                requests.append(self._generate_subcat_request(add_https(subcat)))
        else:
            pagination = response.css('span.list-tool-pagination-text strong::text').extract()
            filtered_pagination = [s for s in pagination if s.isdigit()]
            total_pages = int(max(filtered_pagination))
            curr_page = int(min(filtered_pagination))
            logging.info(total_pages)
            products = response.css('a.item-title::attr(href)').extract()
            # logging.info(products)

            for product in products:
                requests.append(self._generate_product_request(product))

            requests.append(self._generate_page_request(response.url, curr_page, total_pages))

        return requests

    # Parse each page, not yet functional
    def parse_list_products(self, response):
        total_pages = response.meta.get('total_pages')
        curr_page = response.meta.get('curr_page')
        requests = []
        products = response.css('a.item-title::attr(href)').extract()
        url = response.url
        logging.info("HELLO I AM HERE IN PARSE_LIST_PRODUCTS")

        for product in products:
            requests.append(self._generate_product_request(product))

        if curr_page != total_pages:
            curr_page += 1
            if "/p/pl?" in url:
                if "page" in url:
                    new_url = url.replace(f"page={curr_page - 1}", f"page={curr_page}")
                else:
                    new_url = url + "page=" + str(curr_page)
            else:
                if "Page" in url:
                    new_url = url.replace(f"Page-{curr_page - 1}", f"Page={curr_page}")
                else:
                    parts = url.replace('?', '/').split('/')[0:-1]
                    new_url = '/'.join(parts) + '/Page-' + str(curr_page) + url.replace('?', '/').split('/')[-1]

            requests.append(self._generate_page_request(new_url, curr_page, total_pages))

        return requests

    def parse_product(self, response):
        ul_elem = response.css('div.product-bullets ul')
        li_elems = ul_elem.xpath("./li/text()").getall()
        desc = ' '.join([elem.replace('\n', ' ').strip() for elem in li_elems])
        # This also works desc = ' '.join(response.css('div.product-bullets ul').xpath("./li/text()").getall())

        main_price = response.css('div.product-price ul.price li.price-current strong::text').extract()
        cents = response.css('div.product-price ul.price li.price-current sup::text').extract()
        try:
            price = float(main_price[0].replace(',', '.') + cents[0])
        except:
            price = float(main_price[0].replace(',', '.'))

        if response.css('div.product-seller-rating::text').extract():
            rating = response.css('div.product-seller-rating::text').extract()
        else:
            rating = response.css('div.product-seller-rating span::text').extract()
            rating = ' '.join(rating)

        if response.css('div.product-seller a strong::text').extract():
            seller = response.css('div.product-seller a strong::text').extract()[0]
        else:
            seller = response.css('div a.sold-shipped-by-newegg::text').extract()

        id = str(response.css('em::text').extract()[0])

        # Checks if id is in products set, else it checks if products are less than 500
        if id in self.parsed_product_ids:
            logging.info(f'Product details for this id {id} are already parsed!')
        else:
            if len(self.parsed_product_ids) < self.max_products:
                logging.info(f'To be parsed Diamond: {id}')
                l = ItemLoader(NeweggComItem(), response)
                l.add_value('product_title', response.css('h1.product-title::text').extract())
                l.add_value('product_description', desc)
                l.add_value('product_final_pricing', price)
                l.add_value('product_rating', rating)
                l.add_value('seller_name', seller)
                l.add_value('main_image_url',  response.xpath('//img[contains(@id, "mainSlide")]/@src').get())
                # l.add_value('product_url', response.url)

                self.parsed_product_ids.add(id)
                logging.info(f'Done parsing: {id}')
                yield l.load_item()
            else:
                raise CloseSpider('Stopping spider because 500 condition is met')


        # Next page ---- Not yet finished

