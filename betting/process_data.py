

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
    data['same_bet'] = data['offers.id']
    # Mathematically Sensible Odds
    data['odd_math'] = data['oddsDecimal'] - 1.0
    # Seed Fields
    data['min_boost_to_positive'] = np.nan
    data['free_bet_profit_pct'] = np.nan
    data['bet1'] = 100.0 
    data['bet2_30boost_on_pos'] = np.nan
    data['winnings1'] = np.nan
    data['winnings2'] = np.nan
    data['good_bet'] = False


    for bet in data['same_bet'].unique():
        mask = data['same_bet'] == bet
        c_big = data[mask]
        if len(c_big) % 2 == 0:
            pass
            for i in  range(2,len(c_big)+2,2):
                c = c_big[i-2:i]
                data.loc[c.index,'min_boost_to_positive'] = 1/(c['odd_math'].min() * c['odd_math'].max())
                data.loc[c.index, 'free_bet_profit_pct'] = c['odd_math'].max() - c['odd_math'].max() / (c['odd_math'].min() + 1)
            if False:
                boosted_o1 = c['odd_math'].max() * 1.3
                odds_ratio = (boosted_o1 + 1) / (c['odd_math'].min() + 1)
                data.loc[c.index,'bet2_30boost_on_pos'] = c['bet1'].mean() * odds_ratio
                data.loc[c.index,'winnings1'] =  c['bet1'].mean() + c['bet1'].mean() * boosted_o1
                data.loc[c.index,'winnings2'] =  data.loc[c.index,'bet2_30boost_on_pos'] + data.loc[c.index,'bet2_30boost_on_pos'] * (c['odd_math'].min())
    return data


