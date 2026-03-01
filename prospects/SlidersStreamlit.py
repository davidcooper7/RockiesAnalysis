import streamlit as st
import pandas as pd

class Sliders:

    def __init__(self, prospects):
        self.prospects = prospects

    def render(self):
        st.sidebar.header("Adjust Prospect Weights")

        # Store slider values
        raw = {}

        for stat in self.prospects.categories:
            raw[stat] = st.sidebar.slider(
                label=stat,
                min_value=0,
                max_value=100,
                value=0,
                step=1,
                key=f"slider_{stat}"
            )

        # Apply weights
        self.prospects.weigh(raw)

        # Display results
        st.subheader("Rankings")

        df = pd.DataFrame({
            "Player": self.prospects.score_df["Player"],
            "Position": self.prospects.score_df["Position"],
            "Level": self.prospects.score_df["Level"],
            "Rank": self.prospects.score_df["Rank"]
        }).sort_values("Rank")

        st.dataframe(df.head(50), use_container_width=True, hide_index=True)