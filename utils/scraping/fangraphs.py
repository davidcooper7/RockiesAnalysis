import os, sys, requests, io, json
from bs4 import BeautifulSoup
import pandas as pd
sys.path.append('/home/dcooper/rockies/RockiesAnalysis')


def get_player_fangraphs_props(last, first, playerid):
    URL = f'https://www.fangraphs.com/players/{first}-{last}/{playerid}/stats/pitching'
    session = requests.session()
    content = session.get(URL).content
    soup = BeautifulSoup(content)
    next_data = soup.find("script", id="__NEXT_DATA__")
    props = json.loads(next_data.string)

    return props

def get_all_player_fangraphs_props(names, playerids):
    fangraph_props = []
    for (name, playerid) in zip(names, playerids):
        props = get_player_fangraphs_props(*split_name(name), playerid)
        fangraph_props.append(props)

    return fangraph_props
    
def is_pitcher(props):

    pos = props['props']['pageProps']['dataStats']['playerInfo']['Position']
    if pos == 'P':
        return True
    else:
        return False

def get_prospect_data(props, verbose: bool=False):
    try:
        return props['props']['pageProps']['dataCommon']['prospect'][0]
    except:
        if verbose:
            print('Could not find propect info for', props['props']['pageProps']['dataStats']['playerInfo']['firstLastName'])
        return {}


def is_prospect(props):

    service_time = props['props']['pageProps']['dataContractStatus']['serviceTime']
    if service_time == 0 or service_time is None or service_time == '':
        return True
    elif float(service_time) > 0.08:
        return False
    
    if is_pitcher(props):
        if 'data' in props['props']['pageProps']['dataCommon'].keys():
            IP = float(props['props']['pageProps']['dataCommon']['data'][0]['IP'])
            if IP >= 50:
                return False
    else:
        raise NotImplementedError()

    return True


def get_specific_data(in_data, keys):
    out_data = {}
    for key in keys:
        if key in in_data.keys():
            out_data[key] = in_data[key]
        else:
            out_data[key] = np.nan

    return out_data
