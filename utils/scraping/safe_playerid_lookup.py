import os, json
from pybaseball import *

def fangraphs_playerid_lookup(last, first):

    # Missing FanGraphs IDs
    missing_ids = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'additional_fangraph_playerids.json'), 'r'))
    
    # Lookup fangraphs id
    name = ' '.join([first, last])
    try:
        playerid = playerid_lookup(last, first, ignore_accents=True)['key_fangraphs'][0]
    except:
        if name in missing_ids.keys():
            return missing_ids[name]
        else:
            print(f'First: {first}, Last: {last}')
            raise Exception()            
        
    if playerid == -1 or playerid is None:
        if name in missing_ids.keys():
            return missing_ids[name]
        else:
            print(f'First: {first}, Last: {last}')
            display(playerid_lookup(last, first, ignore_accents=True))
            raise Exception()

    return playerid
    


def savant_playerid_lookup(last, first):

    # Missing FanGraphs IDs
    missing_ids = {
        'CJ Cron': 543068,
        'Welinton Herrera': 700327,
        'Gabriel Hughes': 687312,
        'RJ Petit': 696275
    }
    
    # Lookup fangraphs id
    name = ' '.join([first, last])
    try:
        playerid = playerid_lookup(last, first, ignore_accents=True)['key_mlbam'][0]
    except:
        if name in missing_ids.keys():
            return missing_ids[name]
        else:
            print(f'First: {first}, Last: {last}')
            raise Exception()            
        
    if playerid == -1 or playerid is None:
        if name in missing_ids.keys():
            return missing_ids[name]
        else:
            print(f'First: {first}, Last: {last}')
            display(playerid_lookup(last, first, ignore_accents=True))
            raise Exception()

    return playerid