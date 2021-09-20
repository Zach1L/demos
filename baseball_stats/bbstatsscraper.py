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
                if df[col].dtype == np.float64:
                    dtype_sum_dict[col] = sum
                else:
                    dtype_sum_dict[col] = 'first'
            
            if b_or_p == 'b':
                self.batting_df = self.batting_df_raw[mask].groupby('un_name').agg(dtype_sum_dict)
                bb_stat_utils.calc_SLUG_TOT(self.batting_df)
                self.topsis()
            else:
                self.pitching_df = self.pitching_df_raw[mask].groupby('un_name').agg(dtype_sum_dict)
                # TODO Add derived pitching stats here
    
    

    def topsis(self):
        """
        Modified implement ation of https://en.wikipedia.org/wiki/TOPSIS
        """
        cats = ['HR', 'RBI', 'OB_TOT', 'SB', 'SLUG_TOT']
        
        # Normal The Catagories of Interest
        rss = (self.batting_df[cats] ** 2).sum(axis=0) ** 0.5
        cats_norm = self.batting_df[cats] / rss
        
        # The Ideal is the Best Player in Each Catagory
        ideals = cats_norm.max(axis=0)

        # Determine Weights Avoid Overweighting more common (SB much more common than HR )
        ideal_total_points = ideals.sum(axis=0)
        weights = 1 / (cats_norm.max() / ideal_total_points) #Arbitrary Units
        
        # Weighted Distance From Ideals
        distance_from_ideals = ((weights *(cats_norm - ideals)) ** 2).sum(axis=1) ** 0.5
        self.batting_df['distance_from_ideals'] = distance_from_ideals
        self.batting_df.sort_values('distance_from_ideals', ascending=True, inplace=True)
        self.batting_df.to_csv('batter_rankings.csv')
