import os, sys, json
import pandas as pd
import numpy as np
from utils.scraping.rosters import scrape_all_rosters
from utils.scraping.safe_playerid_lookup import load_fangraph_playerids
from utils.scraping.fangraphs import get_age, get_all_player_fangraphs_props


class ProspectScraper():

    def __init__(self, skip_names=[]):

        # Load propsect data
        self.prospect_data_dir = './prospects/data/'
        self.csv_fn = os.path.join(self.prospect_data_dir, 'prospects.csv')
        if os.path.exists(self.csv_fn):
            self.df = pd.read_csv(self.csv_fn)
        else:
            self.skip_names = skip_names
            self._scrape_prospects()


    def _scrape_prospects(self):

        # Create DataFrame
        self.df = pd.DataFrame(columns=['Name', 'Age', 'Level', 'FangraphsID', 'PropsJSON'])

        # Get names and levels
        names, levels = scrape_all_rosters()
        for name in self.skip_names:
            if name in names:
                idx = names.index(name)
                names.pop(idx)
                levels.pop(idx)

        # Get fangraph IDs
        playerids = load_fangraph_playerids(names)

        # Get props from fangraphs
        fangraph_props = get_all_player_fangraphs_props(names, playerids)

        # Iterate through names, get age, and add to DataFrame
        for (name, level, playerid, props) in zip(names, levels, playerids, fangraph_props):

            # Skip, if manually specified
            if name in self.skip_names:
                continue

            # Get age
            age = get_age(props)

            # Store props to .json
            props_json = os.path.join(self.prospect_data_dir, str(playerid) + '.json')
            with open(props_json, 'w') as f:
                json.dump(props, f, indent=4)

            # Add to DataFrame
            self.df.loc[self.df.shape[0]] = [name, age, level, playerid, props_json]

        # Save DataFrame
        self.df.to_csv(self.csv_fn)


    def __iter__(self):
        return zip(*(self.df[col] for col in self.df.columns))


def load_pitching_categories(years=[2024, 2025]):
    pitching_grades = [
        'Position',
        'Level',
        'Age',
        'Range',
        'Touch',
        'FV_Current',
        'pFB',
        'fFB',
        'pSL',
        'fSL',
        'pCB',
        'fCB',
        'pCH',
        'fCH',
        'pCMD',
        'fCMD',
        'Draft_Rnd',
    ]
    levels = ['CPX', 'DSL', 'A', 'A+', 'AA', 'AAA', 'MLB']
    pitching_stats = ['IP', 'K%', 'BB%', 'K/BB', 'HR/9', 'ERA', 'FIP', 'AVG', 'WHIP', 'GB%', 'FB%', 'LD%']
    stat_cols = [f'{level}_{stat}' for level in levels for stat in pitching_stats ]

    return pitching_grades, pitching_stats, stat_cols, years, levels


def load_hitting_categories(years=[2024, 2025]):
    hitting_grades = ['Position', 'Level', 'Age', 'FV_Current', 'pHit', 'fHit', 'pGame', 'fGame', 'pRaw', 'fRaw', 'pSpd', 'fSpd', 'pFld', 'fFld', 'Draft_Rnd']
    levels = ['CPX', 'DSL', 'A', 'A+', 'AA', 'AAA', 'MLB']
    hitting_stats = ['PA', 'AVG', 'BB%', 'K%', 'BB/K', 'OBP', 'SLG', 'OPS', 'ISO', 'BABIP', 'LD%', 'GB%', 'FB%', 'wOBA', 'wRC+']
    stat_cols = [f'{level}_{stat}' for level in levels for stat in hitting_stats ]

    return hitting_grades, hitting_stats, stat_cols, years, levels
