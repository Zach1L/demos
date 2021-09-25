import baseball_ref
import logging
import bb_stat_utils

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)
b = baseball_ref.BaseBallReferenceScraper()
b.compile_stats_year()
b.batting_df.to_csv('all_batting.csv')
b.pitching_df.to_csv('all_pitching.csv')


bb_stat_utils.calc_SLUG_TOT(b.batting_df)
cats = ['HR', 'RBI', 'OB_TOT', 'SB', 'SLUG_TOT']
cats_power = {key: 1.0 for key in cats}
bb_stat_utils.topsis(df=b.batting_df, cats=cats, cats_power=cats_power,  csv_name='bat_rank.csv')

bb_stat_utils.calc_WHIP_TOT(b.pitching_df)
cats = ['ER', 'QS_STAND', 'SV', 'WH_TOT', 'SO', 'IP']
cats_power = {'ER': -1.0, 'QS_STAND': 1.0, 'SV': 1.0, 'WH_TOT': -1.0, 'SO': 1.0, 'IP' : 1.0}
bb_stat_utils.topsis(df=b.pitching_df, cats=cats, cats_power=cats_power, csv_name='pitch_rank.csv')


