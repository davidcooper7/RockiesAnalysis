import os, sys, time
import pandas as pd
from pybaseball import *
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from safe_playerid_lookup import savant_playerid_lookup

def load_pitch_data(start_year=2021, end_year=2025):
    # Load/build database
    data_csv = f'/home/dcooper/rockies/RockiesAnalysis/data/{start_year}-{end_year}_allPitchData.csv'
    if not os.path.exists(data_csv):
        dfs = []
        for year in range(start_year, end_year+1):
            print(f"Pulling {year}...")
            try:
                df = statcast(
                    start_dt=f"{year}-03-01",
                    end_dt=f"{year}-10-31",
                    verbose=False
                )
                dfs.append(df)
                time.sleep(5)  # be nice to Savant
            except Exception as e:
                print(f"Failed for {year}: {e}")
        
        data = pd.concat(dfs, ignore_index=True)
        data.to_csv(data_csv)
    else:
        data = pd.read_csv(data_csv, index_col=0)
    
        # Filter to regular season games
        data = data.loc[data['game_type'] == 'R']
    
    return data


def load_batted_ball_data(start_year=2021, end_year=2025):
    # Load/build database
    data_csv = f'/home/dcooper/rockies/RockiesAnalysis/data/{start_year}-{end_year}_allBattedBall.csv'
    if not os.path.exists(data_csv):
        dfs = []
        for year in range(start_year, end_year+1):
            print(f"Pulling {year}...")
            try:
                df = statcast(
                    start_dt=f"{year}-03-01",
                    end_dt=f"{year}-10-31",
                    verbose=False
                )
                df = df.loc[df['type'] == 'X'] # Get balls in play only
                dfs.append(df)
                time.sleep(5)  # be nice to Savant
            except Exception as e:
                print(f"Failed for {year}: {e}")
        
        data = pd.concat(dfs, ignore_index=True)
        data.to_csv(data_csv)
    else:
        data = pd.read_csv(data_csv, index_col=0)
    
        # Filter to regular season games
        data = data.loc[data['game_type'] == 'R']
    
    return data


def filter_df(df, last=None, first=None, playerid=None, batter: bool=False, home_team=None, not_home_team=None, batter_on_team=None):

    # Get playerid, if necessary
    if playerid is None and last is not None and first is not None:
        playerid = savant_playerid_lookup(last, first)

    # Filter by player
    if batter and playerid is not None:
        df = df.loc[df['batter'] == playerid]

    # Filter by location
    if home_team is not None:
        df = df.loc[df['home_team'] == home_team]
    if not_home_team is not None:
        df = df.loc[df['home_team'] != home_team]

    # Filter by team
    if batter_on_team is not None:
        df = df.loc[(df['home_team'] == batter_on_team & df['inning_topbot'] == 'Bot') | (df['away_team'] == batter_on_team & df['inning_topbop'] == 'Top')]
    

    return df
    











              