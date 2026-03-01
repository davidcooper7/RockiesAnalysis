import os, sys, json
import pandas as pd
import numpy as np
from prospects.ProspectScraper import *
from utils.scraping.fangraphs import *
from utils.scraping.split_name import split_name

class Prospects():
    """
    class to handle data management for pitching prospects
    """

    def __init__(self, years=[2024,2025], skip_names=[], level_weights=np.array([1,1,1,1,1.025,1.05,1.07])):

        # Set skip categories
        self.skip_categories = ['Position', 'Level']
        
        # Save level weights
        self._level_weights = level_weights.copy()
        
        # Load prospects w/ ProspectScraper
        self.scraper = ProspectScraper(skip_names=skip_names)
        self._grades, self._stats, self._stat_cols, self._years, self._levels = self._load(years)

        # Prepare df
        self._init_df()

        # Normalize df
        self._preprocess()
        self._normalize()


    def weigh(self, weights):
        
        # Weigh
        self.w = weights
        self._normalize_weights()
        self._score()

    
    def _load(self):
        return None

    
    def _check(self):
        return False
        
        
    def _init_df(self):
        
        # Build initial df from FanGraphs props
        self.df = pd.DataFrame(columns= self._grades + self._stat_cols)
        for (i, name, age, level, playerid, props_json) in self.scraper:

            # Get props
            props = json.load(open(props_json, 'r'))
            
            # Check if prospect
            if not self._check(props):
                continue

            # Add to DataFrame
            self.df.loc[name] = np.zeros(self.df.shape[1])


            # Propspect props
            prospect_props = get_prospect_data(props)
            if prospect_props != {}:
                pitching_prospect_props = get_specific_data(prospect_props, self._grades)
                for key, item in pitching_prospect_props.items():
                    if key != 'PlayerName':
                        self.df[key].loc[name] = item
            else:
                self.df['Age'].loc[name] = age
                self.df['Position'].loc[name] = get_position(props)

            # Add level
            self.df['Level'].loc[name] = level
            
            # Propsect stats
            prospect_stats = get_stats(props)
            prospect_stats_df = get_stats_df(prospect_stats, name, stat_names=self._stats, stat_cols=self._stat_cols, weigh_stat=self._weigh_stat)
            for col in prospect_stats_df.columns:
                self.df[col].loc[name] = prospect_stats_df[col].loc[name]

            # Check for nonfactors
            if self.df.loc[name].dropna().unique().shape[0] == 1:
                first, last = split_name(name)
                self.df.drop(index=name)
        
    
    def _preprocess(self):
        None


    def _get_categories(self):
        return [c for c in self._norm_df.columns.to_list() if c not in self.skip_categories]
    
    
    def _normalize(self):

        # Normalize into new df
        self._norm_df = pd.DataFrame(index=self.df.index)
        # display(self._norm_df.head())

        # Normalize grades
        self._normalize_grades()
        # display(self._norm_df.head())

        # Normalize stats
        self._normalize_stats()
        # display(self._norm_df.head())

        # Set final categories
        self.categories = self._get_categories()


    def _normalize_vals(self, vals, min, max, label=None):
        norm_vals = (vals - min) / (max - min)
        norm_vals[norm_vals < 0] = np.nan

        return norm_vals


    def _normalize_grades(self):
        None

    def _normalize_stats(self):
        None
        

    def _normalize_weights(self):
        print('THIS IS RUNNING')
        wsum = np.sum([item for _, item in self.w.items()])
        if wsum == 0:
            n = len(self.w)
            self.w = {k: w/n for k, w in self.w.items()}
        else:
            self.w = {k: w/wsum for k, w in self.w.items()}

    
    def _score(self):

        # Add score DataFrame
        self.score_df = pd.DataFrame()
        self.score_df['Player'] = self._norm_df.index.to_list()

        # Get scores
        scores = np.zeros((self._norm_df.shape[0], self._norm_df.shape[1]))
        for i in range(self._norm_df.shape[0]):
            name = self._norm_df.index.to_list()[i]
            vals = {col: float(val) for col, val in zip(self._norm_df.columns.to_list(), self._norm_df.iloc[i].to_list()) if col not in self.skip_categories}
            for j, (k, w) in enumerate(self.w.items()):
                v = vals[k]
                if np.isnan(v):
                    scores[i,j] = np.nan
                else:
                    scores[i,j] = v * w

                
            
        # Add final score and rank to DataFrame
        self.score_df['Position'] = self._norm_df['Position'].to_list()
        self.score_df['Position'].loc[self.score_df['Position'].isin(['SIRP', 'MIRP'])] = 'P'
        self.score_df['Level'] = self._norm_df['Level'].to_list()
        self.score_df['Score'] = np.nansum(scores, axis=1)
        self.score_df['Score'].fillna(0, inplace=True)
        self.score_df['Rank'] = self.score_df['Score'].rank(ascending=False, method='dense').astype(int)
        self.score_df = self.score_df.sort_values('Score', ascending=False)
