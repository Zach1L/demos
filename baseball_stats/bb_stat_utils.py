import pandas as pd
import scipy.stats

def calc_SLUG_TOT(df: pd.DataFrame):
	"""
	Adds slugging percentage related metrics
	df is a pointer to the dataframe, so it doesnt need to be returned
	"""
	df['1B'] = df['H'] - df[['2B','3B','HR']].sum(axis=1)
	df['SLUG_TOT'] = (df[['1B', '2B','3B','HR']] * [1, 2, 3, 4]).sum(axis=1)
	df['OB_TOT'] = df[['1B', '2B','3B','HR', 'BB', 'HBP']].sum(axis=1)

def calc_WHIP_TOT(df: pd.DataFrame):
	"""
	Adds Additional pitching metrics
	df is a pointer to the dataframe, so it doesnt need to be returned
	"""
	# Quality starts is not recorded by baseball reference
	df['WH_TOT'] = df[['BB', 'H']].sum(axis=1)
	df['QS_STAND'] = df['GS'] - df['L']
	df.loc[df['QS_STAND'] < 0, 'QS_STAND'] = 0

def IP_basis_conversion(ip: str):
    ip = float(ip)
    fractional_ip = (ip - int(ip)) / 0.3
    return int(ip) + fractional_ip

def topsis(df: pd.DataFrame, cats: list, cats_power: dict, csv_name: str):
	"""
	Modified implement ation of https://en.wikipedia.org/wiki/TOPSIS
	"""

	# Normalize The Catagories of Interest

	# Correct the metrics so a larger number is always better
	df_corrected_metric = df[cats].apply(lambda x: x ** cats_power[x.name])
	rss = (df_corrected_metric ** 2).sum(axis=0) ** 0.5
	cats_norm = df_corrected_metric / rss
	
	# The Ideal is the Best Player in Each Catagory
	ideals = cats_norm.max(axis=0)

	# Determine Weights Avoid Overweighting more common (SB much more common than HR )
	ideal_total_points = ideals.sum(axis=0)
	weights = 1 / (cats_norm.max() / ideal_total_points) #Arbitrary Units
	
	# Weighted Distance From Ideals
	distance_from_ideals = ((weights *(cats_norm - ideals)) ** 2).sum(axis=1) ** 0.5
	df['distance_from_ideals'] = distance_from_ideals
	df.sort_values('distance_from_ideals', ascending=True, inplace=True)

	if csv_name:
		df.to_csv(csv_name)
	return df.copy()

def ANOVA(df: pd.DataFrame, group: str, metric: str):
	"""
	https://en.wikipedia.org/wiki/One-way_analysis_of_variance
	"""
	m_ingroup = df.groupby(group).mean()[metric]
	count_ingroup = df.groupby(group).count()[metric]
	m_overall = df[metric].mean()

	# Between Groups sum square of differences
	SB = (count_ingroup * (m_ingroup - m_overall) ** 2).sum()

	# Between Group Degree of Freedom
	FB = len(m_ingroup) - 1

	# Between Group Mean Square Value
	MSB =  SB / FB

	# Within Group Sum of Squares
	SW =  sum([((df.loc[df[group] == i, metric] - m_ingroup[i]) ** 2).sum() for i in df[group].unique()])

	# Within Group DoF
	FW = df[group].nunique() * (count_ingroup.median() - 1)

	#Mean square within  gorup
	MSW = SW / FW

	Fstat = MSB / MSW

	Fcrit = scipy.stats.f.ppf(0.95, FB, FW)
	if Fstat > Fcrit:
		print(f'REJECT null hypothesis that all {group} produce the same response in {metric}')
	else:
		print(f'ACCEPT null hypothesis that all {group} produce the same response in {metric}')