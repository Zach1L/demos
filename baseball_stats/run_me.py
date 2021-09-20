import bbstatsscraper
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.DEBUG)
b = bbstatsscraper.BaseBallStatsScraper()
b.compile_stats_year()
