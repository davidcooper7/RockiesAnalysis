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


    def _normalize_weights(self):

        # Compute sums of different categories
        hitting_wsum = np.sum([item for k, item in self.w.items() if k in self.hitting_categories]) / 100
        pitching_wsum = np.sum([item for k, item in self.w.items() if k in self.pitching_categories]) / 100
        both_wsum = np.sum([item for k, item in self.w.items() if k in self.both_categories]) / 100
        wsum = hitting_wsum + pitching_wsum 

        # Correct for division by zero
        for s, c in zip([hitting_wsum, pitching_wsum, both_wsum, wsum], [self.hitting_categories, self.pitching_categories, self.both_categories, self._norm_df.index.to_list()]):
            if s == 0:
                s = 1

        # Normalize
        for k, w in self.w.items():
            if k in self.both_categories:
                self.w[k] = w/both_wsum
            elif k in self.pitching_categories:
                self.w[k] = w/pitching_wsum
            elif k in self.hitting_categories:
                self.w[k] = w/hitting_wsum
                    