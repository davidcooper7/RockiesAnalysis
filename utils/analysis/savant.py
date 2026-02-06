import os, sys, requests
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '../..')
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup


def get_spray_angle(hc_x, hc_y):
    return np.degrees(np.arctan2(hc_x - 125, 199 - hc_y))

    
from utils.scraping.safe_playerid_lookup import savant_playerid_lookup
def filter_df(df, last=None, first=None, playerid=None, batter: bool=False, home_team=None, away_team=None, batter_on_team=None, p_throws=None, pitch_type=None, events=None):

    """
    Filter batted ball data
    """

    # Get playerid, if necessary
    if playerid is None and last is not None and first is not None:
        playerid = savant_playerid_lookup(last, first)

    # Filter by player
    if batter and playerid is not None:
        df = df.loc[df['batter'] == playerid]

    # Filter by location
    if home_team is not None:
        df = df.loc[df['home_team'] == home_team]
    if away_team is not None:
        df = df.loc[df['away_team'] == away_team]

    # Filter by team
    if batter_on_team is not None:
        is_home = (df['home_team'] == batter_on_team) & (df['inning_topbot'] == 'Bot')
        is_away = (df['away_team'] == batter_on_team) & (df['inning_topbot'] == 'Top')
        df = df.loc[is_home | is_away]

    # Filter by pitcher handedness
    if p_throws is not None:
        df = df.loc[df['p_throws'] == p_throws]

    # Filter by pitch
    if pitch_type is not None:
        if type(pitch_type) == list:
            df = df.loc[df['pitch_type'].isin(pitch_type)]
        elif type(pitch_type) == str:
            df = df.loc[df['pitch_type'] == pitch_type]

    # Filter by events
    if events is not None:
        if type(events) == list:
            df = df.loc[df['events'].isin(events)]
        elif type(events) == str:
            df = df.loc[df['events'] == events]
    

    return df


def get_pulled_perc(df):
    """
    Assuming batted ball only data and 'spray_angle' has been computed
    """
    pulled = pd.concat([df.loc[df['stand'] == 'R'].loc[df['spray_angle'] <=-15], df.loc[df['stand'] == 'L'].loc[df['spray_angle'] >=15]], axis=0)
    try:
        return 100 * pulled.shape[0] / df.shape[0]
    except ZeroDivisionError:
        return False


def get_hard_hit_rate(df):
    """
    Assumes df is only of BIP.
    """
    try:
        return 100 * (df.loc[df['launch_speed'] >= 95.0].shape[0] / df.shape[0])
    except ZeroDivisionError:
        return np.nan

def is_barrel(exit_velocity: float, launch_angle: float) -> bool:
    """
    Determine whether a batted ball is a Statcast 'barrel'.

    Parameters
    ----------
    exit_velocity : float
        Exit velocity in mph.
    launch_angle : float
        Launch angle in degrees.

    Returns
    -------
    bool
        True if the batted ball is classified as a barrel, False otherwise.
    """
    EVs = np.arange(98,116)
    deg_uppers = np.linspace(30,50,EVs.shape[0])
    deg_lowers = np.linspace(26,8,EVs.shape[0])

    if exit_velocity >=98 and exit_velocity <=116:
        deg_idx = np.where(np.abs(EVs - exit_velocity) == np.abs(EVs - exit_velocity).min())[0][0]
    elif exit_velocity > 116:
        deg_idx = -1
    else:
        return False

    if launch_angle >= deg_lowers[deg_idx] and launch_angle <= deg_uppers[deg_idx]:
        return True
    else:
        return False


def get_barrel_rate(df):
    """
    Assumes df is only of BIP.
    """
    # Get number of barrels
    barrels = np.array([is_barrel(ls, la) for ls, la in zip(df['launch_speed'].to_numpy(), df['launch_angle'].to_numpy())]).sum()
    try:
        return 100 * (barrels / df.shape[0])
    except ZeroDivisionError:
        return np.nan    