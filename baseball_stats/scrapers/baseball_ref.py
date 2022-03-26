import pandas as pd
from bs4 import BeautifulSoup
import urllib.request
import logging
from . import downloader

def actual_year( year_str:str ) -> bool:
    """
    Filter out Garbage Bottom Row of BB Reference Table
    Needs to explicity return True or False
    """
    try:
        int(year_str)
        return True
    except ValueError:
        return False

def single_major_team_filter( team_str:str ) -> bool:
    """
    Filters out Minor League and TOT columns
    Needs to explicity return True or False
    """  
    if not type(team_str) == str:
        logging.warning(f'Team String {team_str} detected and ignored')
        return False
    if ('-min' in team_str) or ('TOT' in team_str):
        return False
    return True


def sanitize_df( df: pd.DataFrame, human_readable_name: str, unique_name: str, columns_to_drop: list) -> pd.DataFrame:
    """
    Filter the Aquired data frame to the useful stats
    """
    df.drop(columns_to_drop, inplace=True, axis=1)
    df['hr_name'] = human_readable_name
    df['un_name'] = unique_name
    good_rows_mask = df.apply(lambda x: actual_year(x.Year), axis=1)
    df = df[good_rows_mask]
    good_rows_mask = df.apply(lambda x: single_major_team_filter(x.Tm), axis=1)
    df = df[good_rows_mask]

    # Need to Ensure Pandas treats raw stats as integers, or ( floats when required pitching only)
    if 'ERA' not in columns_to_drop:
        int_columns = ['Year', 'Age', 'G', 'PA', 'AB','R','H','2B','3B','HR','RBI','SB','CS','BB','SO','GDP','HBP','SH','SF','IBB']
        df[int_columns] = df[int_columns].astype('int32')
    else:
        int_columns = ['Year', 'Age', 'W' , 'L' , 'G' , 'GS' , 'GF', 'CG' ,'SHO', 'SV', 'H','R','ER','HR','BB','IBB','SO','HBP','BK','WP','BF'] 
        float_columns = ['IP']
        df[int_columns] = df[int_columns].astype('int32')
        df[float_columns] = df[float_columns].astype('float')

    return df

def get_positions_from_soup( soup: BeautifulSoup ):
    """
    Get the Player Positions
    Not stored in a very computer-readable friendly way on the Web
    """
    strongs = soup.find_all('strong', limit=5)
    for i in strongs:
        text = i.find_parent().get_text()
        if 'Position' in text:
            text = text.split(':')[-1]
            text = text.replace(' ','').replace('\n', '')
            text = text.replace(',', 'and')
            return text.split('and')

class BaseBallReferenceScraper( ):
    """
    Use Beautiful Soup to Scrape yearly data from 
    baseball-reference.com
    For Educational Purposes Only
    """
    def __init__(self, player_name_ords: range = range(97, 123)) -> None:
        self.player_urls = []
        self.get_active_players(player_name_ords)

        pitching_df_list, batting_df_list =  downloader.parallel_downloads(self.scrape_player, self.player_urls)

        self.pitching_df_raw = pd.concat(pitching_df_list)
        self.batting_df_raw = pd.concat(batting_df_list)
    

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
        try:
            with urllib.request.urlopen(player_url, timeout=1.0) as page:
                soup = BeautifulSoup(page, 'html.parser')
        except: 
            logging.warn('Error on: ' + player_url)
            return {}
        
        # Get the Player Name from the title of the Webpage
        human_readable_name = soup.find('title').string.split('Stats')[0]
        unique_name = player_url.split('/')[-1][:-6]
        logging.info(human_readable_name)

        # Get the Players Positions
        positions = get_positions_from_soup(soup)

        # TODO A column for 'C', '1B', '2B', '3B', 'SS', 'OF', 'DH', 'P'
        return_packet = {}
        batting_table = soup.find('table', id='batting_standard')
        if batting_table:
            base_df = pd.read_html(str(batting_table))[0]
            columns_to_drop = ['OBP', 'SLG', 'OPS', 'BA', 'OPS+', 'TB']
            return_packet['b'] = sanitize_df(
                base_df, human_readable_name, unique_name, columns_to_drop)
        pitching_table = soup.find('table', id='pitching_standard')
        if pitching_table:
            base_df = pd.read_html(str(pitching_table))[0]
            columns_to_drop = ['W-L%', 'ERA', 'ERA+', 'FIP',
                               'WHIP', 'H9', 'HR9', 'BB9', 'SO9', 'SO/W']
            return_packet['p'] = sanitize_df(
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
                self.batting_df = self.batting_df_raw[mask].groupby('un_name').agg(dtype_sum_dict)
            else:
                self.pitching_df = self.pitching_df_raw[mask].groupby('un_name').agg(dtype_sum_dict)
                