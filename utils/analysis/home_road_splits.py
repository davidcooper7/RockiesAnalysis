import os, sys, requests, io
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '../..')
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

# Find day split inds
def get_day_split_inds(logs):
    """
    Assumes input 'logs' is game log logsframe from team_game_logs() in pybaseball.

    Output is a list of indices where the first list is indices of day 1 on the roadtrip/homestand, and so on...
    """
    
    away_inds = [[] for i in range(11)]
    home_inds = [[] for i in range(11)]
    home_count = 0
    away_count = 0
    last = None
    for i, r in logs.iterrows():
        loc = r['Home']
        if loc == '@':
            if last in ['Home', None]:
                away_count = 1
                home_count = 0
            else:
                away_count += 1
            away_inds[away_count-1].append(i)
            last = 'Away'
        else:
            if last in ['Away', None]:
                home_count = 1
                away_count = 0
            else:
                home_count += 1
            home_inds[home_count-1].append(i)
            last = 'Home'  

    return home_inds, away_inds


def get_batter_splits(last, first, year):
    """
    Get batter's splits from FanGraphs
    """

    cols = [
        # Basic info
        'Season',
        'Handedness',
    
        # Counting stats
        'G',
        'AB',
        'PA',
        'H',
        '1B',
        '2B',
        '3B',
        'HR',
        'R',
        'RBI',
        'BB',
        'IBB',
        'SO',
        'HBP',
        'SF',
        'SH',
        'GIDP',
        'SB',
        'CS',
    
        # Rate stats (traditional)
        'AVG',
    
        # Duplicate section header (drop or keep once)
        'Season_2',
        'Handedness_2',
    
        # Plate discipline & advanced rates
        'BB_pct',
        'K_pct',
        'BB_to_K',
        'AVG_2',
        'OBP',
        'SLG',
        'OPS',
        'ISO',
        'BABIP',
        'wRC',
        'wRAA',
        'wOBA',
        'wRC_plus',
    
        # Duplicate section header (drop or keep once)
        'Season_3',
        'Handedness_3',
    
        # Batted-ball profile
        'GB_to_FB',
        'LD_pct',
        'GB_pct',
        'FB_pct',
        'IFFB_pct',
        'HR_to_FB',
        'IFH_pct',
        'BUH_pct',
    
        # Divider (usually drop)
        'divider',
    
        # Spray angles
        'Pull_pct',
        'Cent_pct',
        'Oppo_pct',
    
        # Divider
        'divider_1',
    
        # Contact quality (BIS)
        'Soft_pct',
        'Med_pct',
        'Hard_pct',
    
        # Divider
        'divider_2',
    
        # Pitch-level
        'Pitches',
        'Balls',
        'Strikes'
    ]
    
    drop_inds = [cols[i] for i in [22,23,37,38,47,51,55]] # Removes extra columns

    
    # Look up playerid
    from utils.scraping.safe_playerid_lookup import fangraphs_playerid_lookup
    playerid = fangraphs_playerid_lookup(last, first)
        
    # Scrape FanGraphs
    URL = f'https://www.fangraphs.com/players/{last}-{first}/{playerid}/splits?position=NP&season={year}&split='
    session = requests.session()
    content = session.get(URL).content
    soup = BeautifulSoup(content)
    tables = soup.find_all('table')

    try:
        df1 = pd.read_html(io.StringIO(str(tables[8])))[0] # Standard
        df1 = df1.loc[df1['Handedness'].isin(['Home', 'Away'])]
        
    except:
        print(URL)
        for i, table in enumerate(tables):
            print(i, table.get_text(strip=True)[:300])
        raise Exception()
    df2 = pd.read_html(io.StringIO(str(tables[10])))[0] # Advanced
    df2 = df2.loc[df2['Handedness'].isin(['Home', 'Away'])]
    df3 = pd.read_html(io.StringIO(str(tables[12])))[0] # Batted Ball
    df3 = df3.loc[df3['Handedness'].isin(['Home', 'Away'])]
    df = pd.concat([df1, df2, df3], axis=1)
    df.columns = cols
    df = df.drop(columns=drop_inds)
    df.insert(0, 'Name', [f'{first} {last}', f'{first} {last}'])

    # Remove percent symbols
    for i, col in enumerate(df.columns):
        if type(df[col].to_numpy()[0]) == str and '%' in df[col].to_numpy()[0]:
            df[col] = df[col].str.replace('%', '', regex=False).astype(float)
    
    return df


def combine_split_years(year_dfs):

    sum_inds = np.array([3,4,5,6,7,8,9,10,11,12,12,13,14,15,16,17,18,19,20,21,32,33,50,51,52])
    AB_inds = np.array([22,26,28,30,31])
    PA_inds = np.array([23,24,25,27,29,34,35])
    BIP_inds = np.array([31,36,37,38,39,40,41,42,43,44,45,46,47,48,49])
    drop_inds = np.array([0,1,2])

    # Build new df
    name = year_dfs[0]['Name'].to_list()[0]
    total_df = pd.DataFrame(index=pd.MultiIndex.from_product([[name], ['Home', 'Away']]), columns=year_dfs[0].columns.to_list()[3:])

    # Combine
    for i, col in enumerate(year_dfs[0].columns):
        if i < 3:
            continue

        # Sum
        if i in sum_inds:
            home_val = 0
            away_val = 0
            for year_df in year_dfs:
                home_val += year_df.loc[year_df['Handedness'] == 'Home', col].to_numpy().astype(float)[0]
                away_val += year_df.loc[year_df['Handedness'] == 'Away', col].to_numpy().astype(float)[0]
                
        # Dot products
        else:
            home_counts = np.zeros(len(year_dfs))
            home_vals = np.zeros(len(year_dfs))
            away_counts = np.zeros(len(year_dfs))
            away_vals = np.zeros(len(year_dfs))
            for j, year_df in enumerate(year_dfs):
                home_vals[j] = year_df.loc[year_df['Handedness'] == 'Home', col].to_numpy().astype(float)[0]
                away_vals[j] = year_df.loc[year_df['Handedness'] == 'Away', col].to_numpy().astype(float)[0]
    
                if i in AB_inds:
                    home_counts[j] = year_df.loc[year_df['Handedness'] == 'Home', 'AB'].to_numpy().astype(float)[0]
                    away_counts[j] = year_df.loc[year_df['Handedness'] == 'Away', 'AB'].to_numpy().astype(float)[0]
                    
                elif i in PA_inds:
                    home_counts[j] = year_df.loc[year_df['Handedness'] == 'Home', 'PA'].to_numpy().astype(float)[0]
                    away_counts[j] = year_df.loc[year_df['Handedness'] == 'Away', 'PA'].to_numpy().astype(float)[0]
                    
                elif i in BIP_inds:
                    home_PA = year_df.loc[year_df['Handedness'] == 'Home', 'PA'].to_numpy().astype(float)[0]
                    home_SO = year_df.loc[year_df['Handedness'] == 'Home', 'SO'].to_numpy().astype(float)[0]
                    home_BB = year_df.loc[year_df['Handedness'] == 'Home', 'BB'].to_numpy().astype(float)[0]
                    home_HBP = year_df.loc[year_df['Handedness'] == 'Home', 'HBP'].to_numpy().astype(float)[0]
                    home_counts[j] = home_PA - home_SO - home_BB - home_HBP
    
                    away_PA = year_df.loc[year_df['Handedness'] == 'Away', 'PA'].to_numpy().astype(float)[0]
                    away_SO = year_df.loc[year_df['Handedness'] == 'Away', 'SO'].to_numpy().astype(float)[0]
                    away_BB = year_df.loc[year_df['Handedness'] == 'Away', 'BB'].to_numpy().astype(float)[0]
                    away_HBP = year_df.loc[year_df['Handedness'] == 'Away', 'HBP'].to_numpy().astype(float)[0]
                    away_counts[j] = away_PA - away_SO - away_BB - away_HBP

            home_val = np.dot(home_counts / home_counts.sum(), home_vals)
            away_val = np.dot(away_counts / away_counts.sum(), away_vals)

        # Add to new dataframe
        total_df.loc[(name, 'Home'), col] = home_val
        total_df.loc[(name, 'Away'), col] = away_val


    return total_df