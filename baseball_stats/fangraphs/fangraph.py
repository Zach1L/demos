
# general python imports
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request
import logging
import numpy as np
import time
import sqlite3 as sql

# Selenium Imports
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
#https://www.selenium.dev/documentation/webdriver/waits/
#https://www.selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html


logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

# Init SQLLite conenction
conn = sql.connect('2021_Baseball-.db')

class waiter():
    def __init__(self) -> None:
        self.n_entries_consec = 0
        self.n_entries_prev = 0

        #TODO this is an input
        self.xpath_str = "//div[@id='root-player-pages']//table"

    def table_loaded(self, driver):
        """
        Checks to see if the table is still loading
        """
        _stats_table = driver.find_element_by_xpath(self.xpath_str)
        n_entries = len(_stats_table.find_elements_by_tag_name('tr'))
        if n_entries == self.n_entries_prev:
            self.n_entries_consec += 1
        else:
            self.n_entries_consec = 0
        self.n_entries_prev = n_entries

        # Seems to be a quirk of the first part of the table loading
        if n_entries == 33: 
            time.sleep(0.2) 

        if (self.n_entries_consec >=5):
            self.reset()
            return True
        #print(n_entries,  self.n_entries_consec)

    def reset(self):
        self.n_entries_consec = 0
        self.n_entries_prev = 0



# For a Pitcher
# specific_playerplayers/max-scherzer/3137/stats?position=P
# https://www.fangraphs.com/players/max-scherzer/3137/game-log?type=1&gds=&gde=&season=2021&position=P


def get_batting_urls(season):
    return get_all_player_urls('bat', season=season)

def get_pitching_urls(season):
    return get_all_player_urls('pit', season=season)  

def get_all_player_urls(stat_type: str, season: int):
    """
    Get the batting or pitching 
    URLs for the top 2000 players in season specified (this will be all players)   
    """

    # This Table Loads in Plain HTML and is simply read with BS4
    all_players_url = f"https://www.fangraphs.com/leaders.aspx?pos=all&stats={stat_type}&lg=all&qual=0&type=8&season={season}&players&page=1_2000"
    with urllib.request.urlopen(all_players_url) as page:
        soup = BeautifulSoup(page, 'html.parser')

    # Find the HTML Table Containing All Player URLS
    # This is Required to form the Daily URL
    table3 = soup.find('table', id='LeaderBoard1_dg1_ctl00').find('tbody').find_all('tr')

    daily_urls = []
    player_names = []
    for row in table3:
        specific_player = row.a.text
        player_dashed = '-'.join(specific_player.split()).replace('.','').replace("'",'').lower()
        position_str = row.a.get('href').split('&')[-1]
        player_id = row.a.get('href').split('=')[-2].split('&')[0]
        if  stat_type == 'bat' and position_str == 'position=P':
            position_str += 'B' # Get Pitcher's Batting
        daily_urls.append(f"https://www.fangraphs.com/players/{player_dashed}/{player_id}/game-log?type=1&gds=&gde=&season={season}&{position_str}")
        player_names.append(player_dashed)
    return daily_urls, player_names


def scrape_pitching_data(season, sql_table=None):
    return scrape_data(get_pitching_urls, season, sql_table=sql_table)

def scrape_batting_data(season, sql_table=None):
    return scrape_data(get_batting_urls, season, sql_table=sql_table)  


def scrape_data(url_provider, season: int, sql_table: str):
    """
    Scrapes the data from Fan Graphs 
    """

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    d = webdriver.Chrome(options=chrome_options)
    _waiter = waiter()

    for daily_url, player_name  in zip(*url_provider(season)):
        logging.info(player_name)
        logging.debug(daily_url)
        t0 = time.time()

        d.get(daily_url)

        # Ensures that at least the summary has loaded (contains the only guaranteed to be in a exact location)
        xpath_str = "//div[@id='root-player-pages']//table/thead/tr[2]"
        try:
            header = WebDriverWait(d, 10).until(EC.text_to_be_present_in_element((By.XPATH, xpath_str), "Total"))
        except exceptions.TimeoutException:
            logging.warning('Timed out on' + daily_url)
            pass
        # Wait For the Table to Finish Loading
        table_loaded = False
        ta = time.time()
        while not table_loaded:
            table_loaded = _waiter.table_loaded(d)
            if time.time() - ta > 10:
                break

        # # This should do the same thing, but is extremely SLOW...
        # WebDriverWait(d, 10).until(_waiter.table_loaded)
        # stats_table = d.find_element_by_xpath(_waiter.xpath_str)
        
        if table_loaded:
            stats_table = d.find_element_by_xpath(_waiter.xpath_str)
            df = pd.read_html(stats_table.get_attribute('outerHTML'), match='Team', skiprows=[1,2], header=0)[0]
            header_mask = df['G'] =='G'
            df = df[np.logical_not(header_mask)]
            df['name'] = player_name
            df['id'] = daily_url.split('/')[5]

            if sql_table:    
                df.to_sql(sql_table, conn, if_exists='append')
            else:
                df.to_csv(player_name + '.csv')
        else:
            logging.warning(f'Timed out on request to {daily_url}')

    d.close()

if __name__ == "__main__":
    scrape_batting_data(season=2021, sql_table='bat')
    scrape_pitching_data(season=2021, sql_table='pit')
    conn.close()