import os, time, itertools, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import multiprocessing as mp
from copy import deepcopy
from pybaseball import *


def get_expected_outcomes():

    # Load/build database
    if not os.path.exists('/home/dcooper/rockies/RockiesAnalysis/data/2020-2025_allBattedBallData.csv'):
        raise Exception('/home/dcooper/rockies/RockiesAnalysis/data/2020-2025_allBattedBallData.csv')
        dfs = []
        for year in range(2020, 2026):
            print(f"Pulling {year}...")
            try:
                df = statcast(
                    start_dt=f"{year}-03-01",
                    end_dt=f"{year}-10-01",
                    verbose=False
                )
                # Keep only balls in play
                df = df[df['type'] == 'X']
                dfs.append(df)
                time.sleep(5)  # be nice to Savant
            except Exception as e:
                print(f"Failed for {year}: {e}")
        
        all_BIP_data = pd.concat(dfs, ignore_index=True)
        all_BIP_data.to_csv('/home/dcooper/rockies/RockiesAnalysis/data/2020-2025_allBattedBallData.csv')
    else:
        all_BIP_data = pd.read_csv('/home/dcooper/rockies/RockiesAnalysis/data/2020-2025_allBattedBallData.csv', index_col=0)
    
    # Filter to regular season games
    all_BIP_data = all_BIP_data.loc[all_BIP_data['game_type'] == 'R']
    
    # Set bins
    ev_labels = np.array(['<80', '80-85', '85-90', '90-95', '95-100', '100-105', '105-110', '>=110'])
    ev_bins = np.array([0,80,85,90,95,100,105,110,999])
    la_labels = np.array(['<10°', '10-25°', '25-35°', '35-50°', '>=50°'])
    la_bins = np.array([-999, 10, 25, 35, 50, 999])
    sa_labels = np.array(['-45 to -27°', '-27 to -9°', '-9 to 9°', '9 to 27°', '27 to 45°'])
    sa_bins = np.array([-999, -27,  -9,  9,  27, 999])
    
    # Add spray angle column
    all_BIP_data.insert(0, 'spray_angle', value=np.degrees(np.arctan2(all_BIP_data['hc_x'] - 125, 199 - all_BIP_data['hc_y'])), allow_duplicates=False)
    
    # Add bin columns 
    all_BIP_data.insert(0, 'launch_speed_bin', value='', allow_duplicates=False)
    all_BIP_data.insert(0, 'launch_angle_bin', value='', allow_duplicates=False)
    all_BIP_data.insert(0, 'spray_angle_bin', value='', allow_duplicates=False)
    
    # Reorder columns
    tgt_cols = ['launch_speed', 'launch_speed_bin', 'launch_angle', 'launch_angle_bin', 'spray_angle', 'spray_angle_bin', 'events', 'home_team', 'hc_x', 'hc_y', 'stand', 'batter', 'game_year'] 
    all_BIP_data = all_BIP_data[tgt_cols]
    
    # Add data to new columns
    all_BIP_data.loc[:,'launch_speed_bin'] = pd.cut(all_BIP_data['launch_speed'], ev_bins, labels=ev_labels, right=False)
    all_BIP_data.loc[:,'launch_angle_bin'] = pd.cut(all_BIP_data['launch_angle'], la_bins, labels=la_labels, right=False)
    all_BIP_data.loc[:,'spray_angle_bin'] = pd.cut(all_BIP_data['spray_angle'], sa_bins, labels=sa_labels, right=False)

    # Build expected outcomes table
    exp_outcomes = pd.DataFrame(columns=['EV', 'LA', 'SA', 'ΔHR', 'Δ3B', 'Δ2B', 'Δ1B', 'ΔOut', 'Bases_nCoors', 'Bases_Coors', 'n_Coors'])
    
    # Check for valid events
    valid_events = [
        'home_run', 'triple', 'double', 'single',
        'field_out', 'sac_fly', 'force_out',
        'double_play', 'grounded_into_double_play',
        'fielders_choice_out', 'fielders_choice',
        'triple_play', 'sac_fly_double_play'
    ]
    all_BIP_data = all_BIP_data.loc[all_BIP_data['events'].isin(valid_events)]
    
    # Iterate through bin type combinations
    for ev_bin, la_bin, sa_bin in itertools.product(ev_labels, la_labels, sa_labels):
    
        # Filter by bin types
        bin_df = all_BIP_data.loc[all_BIP_data['launch_speed_bin'] == ev_bin]
        bin_df = bin_df.loc[bin_df['launch_angle_bin'] == la_bin]
        bin_df = bin_df.loc[bin_df['spray_angle_bin'] == sa_bin]
    
        # Split by location
        c_bin_df = bin_df.loc[bin_df['home_team'] == 'COL']
        nc_bin_df = bin_df.loc[bin_df['home_team'] != 'COL']
    
        # Iterate through outcomes and compute deltas for hits
        nc = []
        c = []
        deltas = []
        for event in ['home_run', 'triple', 'double', 'single', 'out']:
    
            # Get event occurance
            if event == 'out':
                nc_n_event = nc_bin_df.loc[nc_bin_df['events'].isin(['field_out', 'sac_fly', 'force_out', 'double_play', 'grounded_into_double_play', 'fielders_choice_out', 'fielders_choice', 'triple_play', 'sac_fly_double_play'])].shape[0]
                c_n_event = c_bin_df.loc[c_bin_df['events'].isin(['field_out', 'sac_fly', 'force_out', 'double_play', 'grounded_into_double_play', 'fielders_choice_out', 'fielders_choice', 'triple_play', 'sac_fly_double_play'])].shape[0]
            else:
                nc_n_event = nc_bin_df.loc[nc_bin_df['events'] == event].shape[0]
                c_n_event = c_bin_df.loc[c_bin_df['events'] == event].shape[0]
    
            # Convert to probabilities
            try:
                nc_p_event = nc_n_event / nc_bin_df.shape[0]
                c_p_event = c_n_event / c_bin_df.shape[0]
            except ZeroDivisionError:
                deltas.append(np.nan)
                nc.append(np.nan)
                c.append(np.nan)
                continue
    
            # Compute delta probabilities
            d_p_event = c_p_event - nc_p_event
            deltas.append(d_p_event)
            nc.append(nc_p_event)
            c.append(c_p_event)
    
        nc_bases = 4 * nc[0] + 3 * nc[1] + 2 * nc[2] + nc[1]
        c_bases = 4 * c[0] + 3 * c[1] + 2 * c[2] + c[1]
        exp_outcomes.loc[exp_outcomes.shape[0]] = [ev_bin, la_bin, sa_bin]  + deltas + [nc_bases, c_bases] + [c_bin_df.shape[0]]
    
    # Drop NA
    exp_outcomes.dropna(inplace=True)
    
    # Drop anywhere n_Coors < 50
    exp_outcomes = exp_outcomes.loc[exp_outcomes['n_Coors'] >= 50]
    
    # Add delta bases
    d_bases = 4 * exp_outcomes['ΔHR'] + 3 * exp_outcomes['Δ3B'] + 2 * exp_outcomes['Δ2B'] + exp_outcomes['Δ1B']
    exp_outcomes.insert(10, 'ΔBases', d_bases)
    
    # Round 
    exp_outcomes = exp_outcomes.round(2)

    return exp_outcomes, all_BIP_data, ev_labels, la_labels, sa_labels