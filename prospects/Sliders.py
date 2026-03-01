import ipywidgets as widgets
import pandas as pd
import numpy as np
from IPython.display import display

class Sliders():

    def __init__(self, prospects):

        # Save prospects
        self.prospects = prospects

        # Create output
        self.out = widgets.Output()

        # Build sliders
        self.sliders = {
            stat: widgets.FloatSlider(
                value=0,
                min=0, 
                max=100,
                step=1,
                description=stat,
                continuous_update=True
            )
            for stat in self.prospects.categories
        }

        self.sliders['Draft_Rnd'] = widgets.FloatSlider(
                value=100,
                min=0, 
                max=100,
                step=1,
                description='Draft_Rnd',
                continuous_update=True
            )

        self.sliders['ERA'] = widgets.FloatSlider(
                value=50,
                min=0, 
                max=100,
                step=1,
                description='ERA',
                continuous_update=True
            )

        # Connect sliders
        for s in self.sliders.values():
            s.observe(self._update_scores, names="value")

        # Sliders in a vertical column
        sliders_box = widgets.VBox(list(self.sliders.values()))

        # Output will be in its own box
        output_box = widgets.VBox([self.out])

        # Combine sliders and output horizontally
        ui = widgets.HBox([sliders_box, output_box], layout=widgets.Layout(align_items='flex-start'))

        # Display
        display(ui)

        # Initial call
        self._update_scores()


    def _update_scores(self, change=None):
        raw = {stat: self.sliders[stat].value 
               for stat in self.prospects.categories}

        self.prospects.weigh(raw)
    
        with self.out:
            self.out.clear_output(wait=True)
            display(pd.DataFrame({
                "Player": self.prospects.score_df["Player"],
                "Level": self.prospects.score_df["Level"],
                "Position": self.prospects.score_df["Position"],
                "Score": self.prospects.score_df["Score"].round(3),
                "Rank": self.prospects.score_df["Rank"]
            }).head(50))
            
            
        