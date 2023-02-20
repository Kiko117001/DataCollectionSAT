# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import Compose
import logging


def _convert_to_str(value):
    if len(value) > 1:
        logging.info("Item value: %s" % value)
        return str(value)
    else:
        return str(value[0])


def _replace_double_quotes(value):
    return value.replace('"', '')


TITLE = scrapy.Field(
    output_processor=Compose(
        _convert_to_str,
        _replace_double_quotes,
    )
)

DEFAULT = scrapy.Field(
    output_processor=Compose(
        _convert_to_str,
    )
)


class NeweggComItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    product_title = TITLE
    product_description = DEFAULT
    product_final_pricing = DEFAULT
    product_rating = DEFAULT
    seller_name = DEFAULT
    main_image_url = DEFAULT
    # product_url = DEFAULT
