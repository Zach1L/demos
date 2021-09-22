import pandas as pd
from bs4 import BeautifulSoup
import logging

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
