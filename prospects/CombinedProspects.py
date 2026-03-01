from prospects.Prospects import Prospects
from prospects.HitterProspects import HitterProspects
from prospects.PitcherProspects import PitcherProspects
import pandas as pd
import numpy as np

class CombinedProspects(Prospects):

    def __init__(self, years=[2024,2025], skip_names=[], level_weights=np.array([1,1,1,1,1.025,1.05,1.07])):

        # Get hitting/pitching prospect individually
        self.hitting_prospects = HitterProspects(years, skip_names, level_weights)
        self.pitching_prospects = PitcherProspects(years, skip_names, level_weights)
        self.skip_categories = self.pitching_prospects.skip_categories

        # Combine
        self._combine_norm_df()


    def _combine_norm_df(self):
        self._norm_df = self.hitting_prospects._norm_df.combine_first(self.pitching_prospects._norm_df)
        self.categories = self._get_categories()
        self.pitching_categories = [c for c in self.pitching_prospects.categories]
        self.hitting_categories = [c for c in self.hitting_prospects.categories]
        self.both_categories = [c for c in self.pitching_categories if c in self.hitting_categories]
        self.categories_dict = {
            'Prospect Info': ['Age', 'Draft Round', 'Future Value'],
            'Pitching & Hitting Stats': ['AVG', 'K%', 'BB%', 'GB%', 'LD%'],
            'Pitching Grades': [g for g in self.pitching_prospects._grades if g not in self.both_categories + ['Level', 'Position']],
            'Pitching Stats': [s for s in self.pitching_prospects._stats if s not in self.both_categories + ['IP']],
            'Hitting Grades': [g for g in self.hitting_prospects._grades if g not in self.both_categories + ['Level', 'Position']],
            'Hitting Stats': [s for s in self.hitting_prospects._stats if s not in self.both_categories + ['PA']]
        }
    
    
    def _normalize_weights(self):
    
        hitting = {k: v for k, v in self.w.items() if k in self.hitting_categories}
        pitching = {k: v for k, v in self.w.items() if k in self.pitching_categories}
        both = {k: v for k, v in self.w.items() if k in self.both_categories}
    
        def normalize_group(group):
            s = sum(group.values())
            if s == 0:
                return {k: 0 for k in group}
            return {k: v/s for k, v in group.items()}
    
        hitting = normalize_group(hitting)
        pitching = normalize_group(pitching)
        both = normalize_group(both)
    
        # Define category-level weights explicitly
        hitting_share = 0.5
        pitching_share = 0.5
    
        for k in hitting:
            self.w[k] = hitting[k] * hitting_share
    
        for k in pitching:
            self.w[k] = pitching[k] * pitching_share
    
        for k in both:
            self.w[k] = both[k]  # or give its own share