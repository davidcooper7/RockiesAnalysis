import os, sys, json
import pandas as pd
import numpy as np
from prospects.ProspectScraper import *
from prospects.Prospects import Prospects
from utils.scraping.fangraphs import *
from utils.scraping.split_name import split_name

class PitcherProspects(Prospects):
    """
    class to handle data management for pitching prospects
    """

    def __init__(self, years=[2024,2025], skip_names=[], level_weights=np.array([1,1,1,1,1.025,1.05,1.07])):
        self._weigh_stat = 'IP'
        super().__init__(years, skip_names, level_weights)


    def _load(self, years):
        return load_pitching_categories(years)


    def _check(self, props):
        return is_pitcher(props) and is_prospect(props)
        
    
    def _preprocess(self):
        
        # Drop rows w/ all NA
        self.df = self.df.dropna(axis=0, how='all')

        # Change "Range" to "Sits"
        pitcher_ranges = self.df['Range'].to_numpy()
        sits = np.zeros(pitcher_ranges.shape[0])
        for i, pitcher_range in enumerate(pitcher_ranges):
            if type(pitcher_range) == str:
                if len(pitcher_range.strip()) == 0:
                    sits[i] = np.nan
                else:
                    min, max = str(pitcher_range).split('-')
                    sits[i] = np.mean([int(min), int(max)])
            else:
                sits[i] = np.nan
        range_idx = self.df.columns.to_list().index('Range')
        self.df = self.df.drop(['Range'], axis=1)
        self.df.insert(range_idx, 'Sits', sits)

        # Rename columns
        self.df = self.df.rename(columns={
                       'Touch':'Tops',
                       'FV_Current': 'Future Value',
                       'Draft_Rnd': 'Draft Round'
                       })

        # Rename grades
        self._grades[self._grades.index('Range')] = 'Sits'
        self._grades[self._grades.index('Touch')] = 'Tops'
        self._grades[self._grades.index('FV_Current')] = 'Future Value'
        self._grades[self._grades.index('Draft_Rnd')] = 'Draft Round'

        # Fix age == 0
        self.df.loc[self.df['Age'] == 0] = np.nan


    def _normalize_grades(self):
        # Add scout grades
        for grade in self._grades:

            # Skips
            if grade in self.skip_categories:
                self._norm_df[grade] = self.df[grade].to_list()
                continue
            
            # Get values
            vals = self.df[grade].to_numpy().astype(float)
            
            # Find min/max
            if grade == 'Age':
                min, max = 16, 32
            elif grade == 'Sits':
                min, max = 85, 98.2
            elif grade == 'Tops':
                min, max = 85, 102
            elif grade == 'Draft Round':
                vals[vals == 0] = np.nan
                min, max = 1, 20
            else: 
                min, max = 20, 80       

            # Add to normalized DataFrame
            if grade in ['Age', 'Draft Round']:
                self._norm_df[grade] = 1 - self._normalize_vals(vals, min, max, grade)
            else:
                self._norm_df[grade] = self._normalize_vals(vals, min, max, grade)

    
    def _normalize_stats(self):

        # Get weights from IP
        weights = np.zeros((len(self._levels), self.df.shape[0]))
        for j, level in enumerate(self._levels):
            weights[j] = self.df[f'{level}_IP'].to_numpy().astype(float)   
        weights /= np.nansum(weights, axis=0)
        
        # Iterate through stats
        for stat in self._stats:

            # Skip IP
            if stat == 'IP':
                continue

            # Iterate though levels
            stat_by_level = np.zeros((len(self._levels), self.df.shape[0]))
            for j, level in enumerate(self._levels):

                # Get values
                vals = self.df[f'{level}_{stat}'].to_numpy().astype(float)
                
                # Find min, max
                if stat == 'K/BB':
                    min, max = 0, np.inf
                elif stat == 'HR/9':
                    min, max = 0, 3
                elif stat in ['ERA', 'FIP']:
                    min, max = 0, 12
                elif stat == 'AVG':
                    min, max = 0, 1
                elif stat == 'WHIP':
                    min, max = 0, 6
                elif '%' in stat:
                    min, max = 0, 100
                    vals *= 100
                else:
                    raise Exception(f'No normalization for {stat}')
                
                # Clean up
                vals[vals > max] = np.nan
                vals[vals < min] = np.nan
                vals[vals == np.inf] = np.nan
                       
                # Normalize values
                if stat in ['HR/9', 'ERA', 'FIP', 'AVG', 'WHIP', 'FB%', 'LD%', 'BB%']: 
                    norm_vals = 1 - self._normalize_vals(vals, min, max, f'{level}-{stat}')
                else:
                    norm_vals = self._normalize_vals(vals, min, max, f'{level}-{stat}')

                # Weigh values by level 
                level_weighted_vals = norm_vals * self._level_weights[j]
                
                # Weigh by innings pitched
                stat_by_level[j] = level_weighted_vals * weights[j]

            # Add stat to df
            self._norm_df[stat] = np.nansum(stat_by_level, axis=0)

        # Normalize infinities
        self._norm_df.replace([np.inf], 1, inplace=True)
        self._norm_df.replace([-np.inf], 0, inplace=True)
        
