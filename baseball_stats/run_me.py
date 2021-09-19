import bbstatsscraper
import logging

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
b = bbstatsscraper.BaseBallStatsScraper()
b.compile_stats_year()

