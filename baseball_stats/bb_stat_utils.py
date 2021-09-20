import pandas as pd

def calc_SLUG_TOT(df: pd.DataFrame):
	"""
	Adds slugging percentage related metrics
	df is a pointer to the dataframe, so it doesnt need to be returned
	"""
	df['1B'] = df['H'] - df[['2B','3B','HR']].sum(axis=1)
	df['SLUG_TOT'] = (df[['1B', '2B','3B','HR']] * [1, 2, 3, 4]).sum(axis=1)
	df['OB_TOT'] = df[['1B', '2B','3B','HR', 'BB', 'HBP']].sum(axis=1)