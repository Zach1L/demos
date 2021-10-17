import logging

from pandas.core.algorithms import unique
import bb_stat_utils
import pandas as pd
import sqlite3 as sql
import numpy as np
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

# TODO this is much better suit as a notebook

def IP_basis_conversion(ip: str):
    ip = float(ip)
    fractional_ip = (ip - int(ip)) / 0.3
    return int(ip) + fractional_ip

conn = sql.connect('2021_Baseball-final.db')

batting_df = pd.read_sql('SELECT * FROM bat', con=conn)
for col in batting_df.columns:
    batting_df[col] = batting_df[col].astype('int', errors='ignore')
batting_df_sum = batting_df.groupby('name').sum()
batting_df['Datetime'] = pd.to_datetime(batting_df['Date'], format="%Y-%m-%d")
bb_stat_utils.calc_SLUG_TOT(batting_df_sum)
cats = ['HR', 'RBI', 'OB_TOT', 'SB', 'SLUG_TOT']
cats_power = {key: 1.0 for key in cats}




# Pitching 
pitching_df = pd.read_sql('SELECT * FROM pit', con=conn)
for col in pitching_df.columns:
    pitching_df[col] = pitching_df[col].astype('int', errors='ignore')
# Very interesting thing, the decimal place of the innings pitched is in a base 3 unit space 
pitching_df['IP'] = pitching_df['IP'].apply(lambda x: IP_basis_conversion(x))
pitching_df_sum = pitching_df.groupby('name').sum()
bb_stat_utils.calc_WHIP_TOT(pitching_df_sum)
cats = ['ER', 'QS_STAND', 'SV', 'WH_TOT', 'SO', 'IP']
cats_power = {'ER': -1.0, 'QS_STAND': 1.0, 'SV': 1.0, 'WH_TOT': -1.0, 'SO': 1.0, 'IP' : 1.0}



try:
    import seaborn as sns
    import matplotlib.pyplot as plt
    sns.set_context('talk')
    sns.set_style('darkgrid')
    # Total Home Runs per Ball Park
    # Cant find great info to validate this, but this seems to agree with https://www.onlyhomers.com/ballparks
    # fig, ax = plt.subplots(figsize=(32, 9))
    # visitor_mask = batting_df['Opp'].str.contains('@') # Ball Park is in the Opp Column
    # batting_df['Ballpark'] = ''
    # batting_df.loc[visitor_mask, 'Ballpark'] = batting_df.loc[visitor_mask, 'Opp'].apply(lambda x: x[1::])
    # batting_df.loc[batting_df['Ballpark'] == '', 'Ballpark'] = batting_df.loc[batting_df['Ballpark'] == '', 'Team'] 
    # df = batting_df.groupby('Ballpark').sum().reset_index()
    # df.sort_values(by='HR', inplace=True)
    # print(df[['Ballpark', 'HR']])
    # sns.barplot(data=df, x='Ballpark', y='HR', ax=ax)
    # plt.savefig('meme.png')


    # Race Plots
    race_y = 'SB'
    race_x = 'Team'
    race_hue = 'Team'
    n_leaders = 10


    #     
    # optional Mask to get every nth day
    n = 7
    batting_df['days'] = (batting_df['Datetime'] - batting_df.iloc[0]['Datetime']).dt.days
    maskii = batting_df['days'] % n == 0

    # Filter to only The leaders in the catagory
    leaders = batting_df[[race_y, race_x]].groupby(race_x).sum().reset_index().sort_values(by=race_y, ascending=False).iloc[:n_leaders]
    mask = [batting_df[race_x] == _race_x for _race_x in leaders[race_x]]
    mask = pd.concat(mask, axis=1).any(axis=1)
    race = batting_df.loc[mask]
    race.sort_values(by='Datetime', ascending=True, inplace=True)

    # Determin the Cummalative Sum of the Catagory
    for _i in race[race_x].unique():
        maski = race[race_x] == _i
        race.loc[maski, 'c' + race_y] = race.loc[maski ,race_y].cumsum()

    fig, ax = plt.subplots(figsize=(16, 9))
    sns.lineplot(data=race, x='Datetime', y='c' + race_y, hue=race_hue, ax=ax)
    plt.xticks(rotation = -45) 
    plt.savefig(race_y + race_x +'race.png')

except ImportError:
    logging.warn('Plots not generated')