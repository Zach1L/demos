import baseball_ref
import logging
import bb_stat_utils
import os
import pandas as pd

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)

if os.path.exists('all_batting.csv') and os.path.exists('all_pitching.csv'):
    batting_df = pd.read_csv('all_batting.csv')
    pitching_df = pd.read_csv('all_pitching.csv')
else:
    b = baseball_ref.BaseBallReferenceScraper()
    b.compile_stats_year()
    b.batting_df.to_csv('all_batting.csv')
    b.pitching_df.to_csv('all_pitching.csv')
    batting_df = b.batting_df
    pitching_df = b.pitching_df



bb_stat_utils.calc_SLUG_TOT(batting_df)
cats = ['HR', 'RBI', 'OB_TOT', 'SB', 'SLUG_TOT']
cats_power = {key: 1.0 for key in cats}
bb_stat_utils.topsis(df=batting_df, cats=cats, cats_power=cats_power,  csv_name='bat_rank.csv')

bb_stat_utils.calc_WHIP_TOT(pitching_df)
cats = ['ER', 'QS_STAND', 'SV', 'WH_TOT', 'SO', 'IP']
cats_power = {'ER': -1.0, 'QS_STAND': 1.0, 'SV': 1.0, 'WH_TOT': -1.0, 'SO': 1.0, 'IP' : 1.0}
bb_stat_utils.topsis(df=pitching_df, cats=cats, cats_power=cats_power, csv_name='pitch_rank.csv')


# ANOVA EXAMPLE (Does Last name effect RBI)
batting_df['last_name'] = batting_df['hr_name'].str.split(' ', expand=True)[1].str[0].str.upper()
batting_df = batting_df[batting_df['PA'] > 200]
bb_stat_utils.ANOVA(batting_df, group='last_name', metric='RBI')

try:
    import seaborn as sns
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(32, 9))
    sns.stripplot(data=batting_df, x='last_name', y='RBI', ax=ax)
    plt.savefig('meme.png')
except ImportError:
    logging.warn('Plots not generated')