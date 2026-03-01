import os, sys, json
import pandas as pd
import numpy as np
from prospects.ProspectScraper import *
from prospects.Prospects import Prospects
from utils.scraping.fangraphs import *
from utils.scraping.split_name import split_name

class HitterProspects(Prospects):
    """
    class to handle data management for pitching prospects
    """

    def __init__(self, years=[2024,2025], skip_names=[], level_weights=np.array([1,1,1,1,1.025,1.05,1.07])):
        self._weigh_stat = 'PA'
        super().__init__(years, skip_names, level_weights)
        


    def _load(self, years):
        return load_hitting_categories(years)


    def _check(self, props):
        return (not is_pitcher(props)) and is_prospect(props)
        
    
    def _preprocess(self):

        # Drop rows w/ all NA
        self.df = self.df.dropna(axis=0, how='all')

        # Fix age == 0
        self.df.loc[self.df['Age'] == 0] = np.nan


    def _normalize_grades(self):
        # Add scout grades
        for grade in self._grades:

            # Skips
            if grade in self.skip_categories:
                self._norm_df[grade] = self.df[grade]
                continue
            
            # Get values
            vals = self.df[grade].to_numpy().astype(float)
            
            # Find min/max
            if grade == 'Age':
                min, max = 16, 32
            elif grade == 'Draft_Rnd':
                vals[vals == 0] = np.nan
                min, max = 1, 20
            else: 
                min, max = 20, 80       

            # Add to normalized DataFrame
            if grade in ['Age', 'Draft_Rnd']:
                self._norm_df[grade] = 1 - self._normalize_vals(vals, min, max, grade)
            else:
                self._norm_df[grade] = self._normalize_vals(vals, min, max, grade)

    
    def _normalize_stats(self):

        # Get weights from PA
        weights = np.zeros((len(self._levels), self.df.shape[0]))
        for j, level in enumerate(self._levels):
            weights[j] = self.df[f'{level}_PA'].to_numpy().astype(float)   
        weights /= np.nansum(weights, axis=0)
        
        # Iterate through stats
        for stat in self._stats:

            # Skip PA
            if stat == 'PA':
                continue

            # Iterate though levels
            stat_by_level = np.zeros((len(self._levels), self.df.shape[0]))
            for j, level in enumerate(self._levels):

                # Get values
                vals = self.df[f'{level}_{stat}'].to_numpy().astype(float)
                
                # Find min, max
                if stat == 'BB/K':
                    min, max = 0, np.inf
                elif stat in ['AVG', 'BABIP']:
                    min, max = 0, 0.400 
                elif stat in ['OBP', 'wOBA']:
                    min, max = 0, 0.500
                elif stat in ['OPS', 'SLG']:
                    min, max = 0, 2.000
                elif stat == 'ISO':
                    min, max = 0, 0.500
                elif stat == 'wRC+':
                    min, max = 20, 180
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
                if stat in ['K%', 'GB%']: 
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
        
