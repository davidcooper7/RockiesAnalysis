import os, sys, requests, io, json
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from utils.scraping.split_name import split_name


def get_player_fangraphs_props(last, first, playerid):
    URL = f'https://www.fangraphs.com/players/{first}-{last}/{playerid}/stats/pitching'
    session = requests.session()
    content = session.get(URL).content
    soup = BeautifulSoup(content)
    next_data = soup.find("script", id="__NEXT_DATA__")
    props = json.loads(next_data.string)

    return props


def get_all_player_fangraphs_props(names, playerids):
    fangraph_props = []
    for (name, playerid) in zip(names, playerids):
        props = get_player_fangraphs_props(*split_name(name), playerid)
        fangraph_props.append(props)

    return fangraph_props


def get_position(props):
    return props['props']['pageProps']['dataStats']['playerInfo']['Position']

    
def is_pitcher(props):
    pos = get_position(props)
    if pos == 'P':
        return True
    else:
        return False


def get_prospect_data(props, verbose: bool=False):
    try:
        return props['props']['pageProps']['dataCommon']['prospect'][0]
    except:
        if verbose:
            print('Could not find propect info for', props['props']['pageProps']['dataStats']['playerInfo']['firstLastName'])
        return {}


def get_age(props):
    return int(props['props']['pageProps']['dataStats']['playerInfo']['Age'])


def is_prospect(props):

    service_time = props['props']['pageProps']['dataContractStatus']['serviceTime']
    if service_time == 0 or service_time is None or service_time == '':
        return True
    elif float(service_time) > 0.08:
        return False


def get_specific_data(in_data, keys):
    out_data = {}
    for key in keys:
        if key in in_data.keys():
            out_data[key] = in_data[key]
        else:
            out_data[key] = np.nan

    return out_data


def get_stats(props):
    return props['props']['pageProps']['dataStats']['data']


def get_stats_df(stats, 
                 player_name, 
                 levels=['CPX', 'DSL', 'A', 'A+', 'AA', 'AAA', 'MLB'], 
                 years=[2024,2025], 
                 stat_names=[],
                 stat_cols=[],
                 weigh_stat='IP'):

    # Get stats for each year in year
    player_year_df = pd.DataFrame(index=[f'{year}_{player_name}' for year in years], columns=stat_cols)
    for season_data in stats:
    
        # Get "seasons"
        if season_data['aseason'] in years and season_data['ateam'] != 'Average':

            # Remove spring training
            if '(ST)' in season_data['ateam']:
                continue

            # Find level
            level = season_data['AbbLevel']
            if level not in levels:
                continue

            # Find year
            year = season_data['aseason']
            # print('Found', year, level)
            
            # Get stats
            for stat in stat_names:
                if stat in season_data.keys():
                    val = season_data[stat]
                else:
                    val = np.nan
                try:
                    player_year_df[f'{level}_{stat}'].loc[f'{year}_{player_name}'] = val
                except:
                    raise Exception(season_data['ateam'])
    
    # Combine years
    player_df = pd.DataFrame(index=[player_name], columns=stat_cols)
    for level in levels:
        for stat in stat_names:

            # Get weights
            Xs = player_year_df[f'{level}_{weigh_stat}'].to_numpy().astype(float)
         
            if np.all(np.isnan(Xs)):
                continue
            else:
                weights = Xs / np.nansum(Xs)

            # Add stat
            if stat == weigh_stat:
                player_df[f'{level}_{stat}'].loc[player_name] = np.nansum(Xs)
            else:
                player_df[f'{level}_{stat}'].loc[player_name] = np.nansum([w*v for w, v in zip(weights, player_year_df[f'{level}_{stat}'].to_numpy())])

    return player_df