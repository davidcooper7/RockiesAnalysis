import os, sys, requests, io, json
import streamlit as st
from copy import deepcopy
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')


# Page Title
st.set_page_config(page_title='Rockies Prospects UI - BETA', layout='wide')

# Page header
with st.container():
    st.subheader("Rockies Prospects Custom Rankings")
    st.markdown("""
    Adjust the scouting and statistical weights in the sidebar to dynamically
    re-rank Rockies prospects. Rankings update instantly based on your preferences.

    Each grade/stat is presentated as on a 0 to 100 scale:\n
    0 means you do not care about that category! \n
    100 means you care about that category the most! 
    """)

@st.cache_resource
def load_propsects():
    from prospects.CombinedProspects import CombinedProspects
    return CombinedProspects(skip_names=['Ethan Cole', 'Izeah Muniz', 'Brady Parker', 'Cam Hassert', 'Kyle Fossum'])

prospects = load_propsects()

from prospects.SlidersStreamlit import Sliders
sliders = Sliders(prospects)
sliders.render()

    
    