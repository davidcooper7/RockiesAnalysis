import streamlit as st
import pandas as pd
import json, os
from pathlib import Path

base_path = Path(__file__).resolve().parent
labels = json.load(open(os.path.join(base_path,  'slider_labels.json'), 'r'))

class Sliders:

    def __init__(self, prospects):
        self.prospects = prospects

    def render(self):

        # Store slider values
        raw = {}

        for group in self.prospects.categories_dict.keys():
            st.sidebar.markdown(f'## {group}')
            for stat in self.prospects.categories_dict[group]:
                st.sidebar.markdown(f'**{stat}** *({labels[stat]})*' )
                raw[stat] = st.sidebar.slider(
                    label='',
                    min_value=0,
                    max_value=100,
                    value=0,
                    step=1,
                    key=f"slider_{stat}"
                )

        # Apply weights
        self.prospects.weigh(raw)

        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
        
        # Build dataframe
        df = pd.DataFrame({
            "Rank": self.prospects.score_df["Rank"],
            "Prospect": self.prospects.score_df["Player"],
            "Position": self.prospects.score_df["Position"],
            "Level": self.prospects.score_df["Level"],
        }).sort_values("Rank").head(50)

        # Custom css
        custom_css = {
            # Remove outer border glow
            ".ag-root-wrapper": {
                "border": "none !important"
            },
        
            # Header background
            ".ag-header": {
                "background-color": "#eeeeee !important",
                "border-bottom": "2px solid #cccccc !important"
            },
        
            # Individual header cells
            ".ag-header-cell": {
                "background-color": "#eeeeee !important",
                "border-right": "1px solid #dddddd !important"
            },
        
            # Header text styling
            ".ag-header-cell-text": {
                "color": "#222222 !important",
                "font-weight": "700 !important",
                "font-size": "16px !important"
            },
        
            # Center header labels
            ".ag-header-cell-label": {
                "justify-content": "center !important"
            },
        
            # Body rows
            ".ag-row-even": {
                "background-color": "#ffffff !important"
            },
            
            ".ag-row-odd": {
                "background-color": "#eeeeee !important"
            },
        
            # Cell text
            ".ag-cell": {
                "color": "#222222 !important",
                "font-size": "15px !important"
            },
        
            # Hover effect (subtle)
            ".ag-row-hover": {
                "background-color": "#f7f7f7 !important"
            }
        }

        # Bubble header
        from st_aggrid import JsCode
        bubble_header = JsCode("""
        class BubbleHeader {
            init(params) {
                this.eGui = document.createElement('div');
                this.eGui.style.width = '100%';
                this.eGui.style.textAlign = 'center';
                this.eGui.style.display = 'flex';
                this.eGui.style.alignItems = 'center';
                this.eGui.style.justifyContent = 'center';
                this.eGui.style.height = '100%';
        
                const pill = document.createElement('span');
                pill.innerText = params.displayName;
                pill.style.backgroundColor = '#2f2f63';
                pill.style.color = 'white';
                pill.style.padding = '14px 32px';   // 🔥 bigger vertical + horizontal padding
                pill.style.borderRadius = '30px';
                pill.style.fontWeight = '700';
                pill.style.fontSize = '20px';       // 🔥 bigger font
                pill.style.display = 'inline-block';
        
                this.eGui.appendChild(pill);
            }
        
            getGui() {
                return this.eGui;
            }
        }
        """)


        
        # Configure grid
        gb = GridOptionsBuilder.from_dataframe(df)
        
        gb.configure_column("Rank", width=90)
        gb.configure_column("Prospect", width=260)
        gb.configure_column("Position", width=110)
        gb.configure_column("Level", width=130)
        
        for col in df.columns:
            gb.configure_column(
                col,
                headerComponentParams=None,
                headerComponent=bubble_header
            )
        
        gb.configure_default_column(
            sortable=True,
            filter=False,
            resizable=True
        )
        
        gb.configure_grid_options(
            pagination=False,
            headerHeight=100
        )
        
        grid_options = gb.build()
        
        AgGrid(
            df,
            gridOptions=grid_options,
            theme="light",  # light works better here
            height=42 * len(df) + 70,
            custom_css=custom_css,
            allow_unsafe_jscode=True
        )
