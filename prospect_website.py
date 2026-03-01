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
    st.subheader("Rockies Prospects!")

@st.cache_resource
def load_propsects():
    from prospects.CombinedProspects import CombinedProspects
    return CombinedProspects(skip_names=['Ethan Cole', 'Izeah Muniz', 'Brady Parker', 'Cam Hassert', 'Kyle Fossum'])

prospects = load_propsects()

from prospects.SlidersStreamlit import Sliders
sliders = Sliders(prospects)
sliders.render()

    
    