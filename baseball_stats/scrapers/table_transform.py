import pandas as pd

UNIQUE_POS = ['fDH', 'fC', 'f1B', 'F2B', 'fSS', 'f3B', 'fPH', 'fLF', 'fCF', 'fRF']
HITTING_COLS =  ["G","AB","PA","H","1B","2B","3B","HR","R","RBI","BB","IBB","SO","HBP","SF","SH","GDP","SB","CS"]
PITCHING_COLS =  ["GS", "W","L", "G","CG","ShO","SV","HLD","BS", "TBF","H","R","ER","HR","BB","IBB","HBP","WP","BK","SO"]

def table_transform(raw_df: pd.DataFrame, player_name: str, daily_url: str, sql_table: str) -> pd.DataFrame:
    """
    Takes the raw data fangraphs table and transforms data to more workable 
    """
    # Remove rows only used for readability onsite
    header_mask = raw_df['G'] =='G'
    df = raw_df[~header_mask].copy()
    df.drop(labels=['divider'], axis=1, inplace=True)

    # Usable Datetime
    df['datetime'] = pd.to_datetime(df['Date'], format="%Y-%m-%d")
    df.drop(labels=['Date'], axis=1, inplace=True)

    # Ad name and unique Player ID colummns
    df['name'] = player_name
    df['id'] = daily_url.split('/')[5]

    if sql_table == 'pit':
        return pitching_transform(df)
    return batting_transform(df)

def IP_basis_conversion(ip: str) -> float:
    ip = float(ip)
    fractional_ip = (ip - int(ip)) / 0.3
    return int(ip) + fractional_ip

def pitching_transform(df: pd.DataFrame) -> pd.DataFrame:
    
    # Cast to Integers (Almosts all Numeric Pitching are integers)
    for col in PITCHING_COLS:
        df[col] = df[col].astype('int')

    df['IP'] = df['IP'].apply(lambda x: IP_basis_conversion(x))
    
    df.drop(labels=['ERA', 'divider.1', 'GS.1'], axis=1, inplace=True)

    return df


def batting_transform(df: pd.DataFrame) -> pd.DataFrame:
    
    for col in HITTING_COLS:
        df[col] = df[col].astype('int')
        
    df[UNIQUE_POS] = 0

    for pos in UNIQUE_POS:
        df.loc[df['Pos'] == pos[1::], pos] = 1

    # Add Aggregate OF Position (RF/CF/LF) being interchangeable
    df['fOF'] = df[['fRF', 'fCF', 'fLF']].sum(axis=1).astype(int)
    
    df.drop(labels=['AVG'], axis=1, inplace=True)

    return df