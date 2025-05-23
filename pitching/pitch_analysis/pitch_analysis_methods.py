from pybaseball import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')


"""
METHODS
"""

def get_player_data(first_name, last_name):

    # Get statcast data
    player_ids = playerid_lookup(last_name, first_name)
    statcast_player_id = player_ids['key_mlbam'][0]
    start_year = int(player_ids['mlb_played_first'])
    finish_year = int(player_ids['mlb_played_last'])
    player_data = statcast_pitcher(f'{start_year}-01-01', f'{finish_year}-12-31', statcast_player_id)
    player_data = player_data[player_data['game_type'] != 'S']

    return player_data


def get_player_pitch_types(player_data):
    return [pitch for pitch in player_data['pitch_type'].unique() if type(pitch) is str]

def parse_data(data, year=None, pitch=None, loc=None):
    if year is not None:
        year_inds = [i for i in range(data.shape[0]) if data['game_date'].iloc[i].startswith(year)]
        data = data.iloc[year_inds, :]    
    if pitch is not None:
        data = data[data['pitch_type'] == pitch]
    if loc == 'home':
        data = data[data['home_team'] == 'COL']
    elif loc == 'away':
        data = data[data['away_team'] == 'COL']

    return data
    

    
