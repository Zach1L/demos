

import re
import urllib.request
import json
import numpy as np
import pandas as pd
import re


def process_betting_data(json_data):
    raw_data = pd.json_normalize(data=json_data['events'], meta=['name', 'startDate', ['offers','id'], ['offers','label']],record_path=['offers', 'outcomes'])
    data = raw_data


    # Group bet ID
    data['same_bet'] = data['id'].apply(lambda x:''.join(re.split('P|N|O|U', x.split('_')[-2])))
    # Mathematically Sensible Odds
    data['odd_math'] = data['oddsDecimal'] - 1.0
    # Seed Fields
    data['bet1'] = 100.0 
    data['bet2_30boost_on_pos'] = np.nan
    data['winnings1'] = np.nan
    data['winnings2'] = np.nan
    data['good_bet'] = False
    data['min_boost_to_positive'] = np.nan
    data['min_boost_to_negitive'] = np.nan


    # https://www.wolframalpha.com/input/?i=%28a%2Bx%29+%2F+%28a%2B1%2Bx%29+%3D+1+%2F%28b%2B1%29++for+x
    for bet in data['same_bet'].unique():
        mask = data['same_bet'] == bet
        c = data[mask]
        if len(c) ==2:
            data.loc[mask,'min_boost_to_positive'] = 1/c['odd_math'].min() - c['odd_math'].max()
            data.loc[mask,'min_boost_to_negitive'] = 1/c['odd_math'].max() - c['odd_math'].min()

            data.loc[mask,'bet2_30boost_on_pos'] = c['bet1'].mean() * (c['odd_math'].max() + 1 + 0.30) / (c['odd_math'].min() + 1)
            data.loc[mask,'winnings1'] =  c['bet1'].mean() + c['bet1'].mean() * (c['odd_math'].max() + 0.30)
            data.loc[mask,'winnings2'] =  data.loc[mask,'bet2_30boost_on_pos'] + data.loc[mask,'bet2_30boost_on_pos'] * (c['odd_math'].min())

    return data


