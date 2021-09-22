import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import urllib.request
import scrape_utils
import logging
import bb_stat_utils
import concurrent.futures

class BaseBallStatsScraper():

    def __init__(self) -> None:
        self.player_urls = []
        self.batting_df_list = []
        self.pitching_df_list = []

        self.get_active_players()

        self.parallel_downloads()

        self.pitching_df_raw = pd.concat(self.pitching_df_list)
        self.batting_df_raw = pd.concat(self.batting_df_list)
    
    def parallel_downloads(self):
        """
        Download / Sanatize Data in Parallel 
        """
        with concurrent.futures.ProcessPoolExecutor(max_workers=8) as executor:
            results = executor.map(self.scrape_player, self.player_urls)

        for _dict in results:
            if 'p' in _dict.keys():
                self.pitching_df_list.append(_dict['p'])
            if 'b' in _dict.keys():
                self.batting_df_list.append(_dict['b'])

    def get_active_players(self, ords: range = range(97, 123)):
        """
        Gets the URLS off all active players populates a list to be parsed
        """
        for last_name_number in ords:
            last_name_letter = chr(last_name_number)
            with urllib.request.urlopen(rf'https://www.baseball-reference.com/players/{last_name_letter}/') as page:
                soup = BeautifulSoup(page, 'html.parser')
            # Player in bold (ie <b> are active)
            self.player_urls += ['https://www.baseball-reference.com' +
                                 i.a.get('href') for i in soup.find_all('b')]
        print(f'{len(self.player_urls)} URLS found!')

    def scrape_player(self, player_url) -> None:
        """
        Given a player URL scrape and santize statistical data to a dataframe
        """
        with urllib.request.urlopen(player_url) as page:
            soup = BeautifulSoup(page, 'html.parser')

        # Get the Player Name from the title of the Webpage
        human_readable_name = soup.find('title').string.split('Stats')[0]
        unique_name = player_url.split('/')[-1][:-6]
        logging.info(human_readable_name)

        # Get the Players Positions
        positions = scrape_utils.get_positions_from_soup(soup)
        # TODO A column for 'C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'P'

        return_packet = {}
        batting_table = soup.find('table', id='batting_standard')
        if batting_table:
            base_df = pd.read_html(str(batting_table))[0]
            columns_to_drop = ['OBP', 'SLG', 'OPS', 'BA', 'OPS+', 'TB']
            return_packet['b'] = scrape_utils.sanitize_df(
                base_df, human_readable_name, unique_name, columns_to_drop)
        pitching_table = soup.find('table', id='pitching_standard')
        if pitching_table:
            base_df = pd.read_html(str(pitching_table))[0]
            columns_to_drop = ['W-L%', 'ERA', 'ERA+', 'FIP',
                               'WHIP', 'H9', 'HR9', 'BB9', 'SO9', 'SO/W']
            return_packet['p'] = scrape_utils.sanitize_df(
                base_df, human_readable_name, unique_name, columns_to_drop)
        return return_packet

    def compile_stats_year(self, year=2021):
        # Filter to a Given Year

        for b_or_p, df in zip(['b', 'p'], [self.batting_df_raw, self.pitching_df_raw]):
            mask = df['Year'] == year

            # Sum the Player Across Multiple Teams (Accounts for Trades)
            # Create A Dictionary to Denote Items that should not be summed
            dtype_sum_dict = {}
            for col in df.columns:
                if df[col].dtype != object:
                    dtype_sum_dict[col] = sum
                else:
                    dtype_sum_dict[col] = 'last'
            
            if b_or_p == 'b':
                # TODO Verify this with Trea
                self.batting_df = self.batting_df_raw[mask].groupby('un_name').agg(dtype_sum_dict)
                bb_stat_utils.calc_SLUG_TOT(self.batting_df)
                cats = ['HR', 'RBI', 'OB_TOT', 'SB', 'SLUG_TOT']
                cats_power = {key: 1.0 for key in cats}
                bb_stat_utils.topsis(df=self.batting_df, cats=cats, cats_power=cats_power,  csv_name='bat_rank.csv')
                
            else:
                # TODO Verify this with Max Scherzer
                self.pitching_df = self.pitching_df_raw[mask].groupby('un_name').agg(dtype_sum_dict)
                bb_stat_utils.calc_WHIP_TOT(self.pitching_df)
                cats = ['ER', 'QS_STAND', 'SV', 'WH_TOT', 'SO', 'IP']
                cats_power = {'ER': -1.0, 'QS_STAND': 1.0, 'SV': 1.0, 'WH_TOT': -1.0, 'SO': 1.0, 'IP' : 1.0}
                bb_stat_utils.topsis(df=self.pitching_df, cats=cats, cats_power=cats_power, csv_name='pitch_rank.csv')



