import os, sys, requests, io
from bs4 import BeautifulSoup
import pandas as pd
sys.path.append('/home/dcooper/rockies/RockiesAnalysis')


## Scraping current rosters
def scrape_roster(URL=None, level=None):

    if URL is None and level is not None:
        if level == 'MLB':
            URL = 'https://www.mlb.com/rockies/roster/40-man'
        elif level == 'AAA':
            URL = 'https://www.milb.com/albuquerque/roster'
        elif level == 'AA':
            URL = 'https://www.milb.com/hartford/roster'
        elif level == 'A+':
            URL = 'https://www.milb.com/spokane/roster'
        elif level == 'A':
            URL = 'https://www.milb.com/fresno/roster'
        elif level == 'ACL':
            URL = 'https://www.milb.com/arizona-complex/roster/1994'
        elif level == 'DSL':
            URL = 'https://www.milb.com/dominican-summer/roster/629'

    session = requests.session()
    content = session.get(URL).content
    soup = BeautifulSoup(content)
    tables = soup.find_all('table')
    names = []
    for table in tables:
        html = str(table)
        if 'mlb' not in URL:
            html = html.replace("<tbody>", "<tbody><tr>").replace("</td>\n<tr>", "</td></tr><tr>")
        df = pd.read_html(io.StringIO(html))[0]
        if df.columns[0] == 'Manager/Coach':
            continue
        col = df.iloc[:,1]
        for r in col:
            name = ' '.join(r.split()[:2])
            names.append(name)

    return names

def scrape_all_rosters():
    MLB_URL = 'https://www.mlb.com/rockies/roster/40-man'
    AAA_URL = 'https://www.milb.com/albuquerque/roster'
    AA_URL = 'https://www.milb.com/hartford/roster'
    HighA_URL = 'https://www.milb.com/spokane/roster'
    A_URL = 'https://www.milb.com/fresno/roster'
    ACL_URL = 'https://www.milb.com/arizona-complex/roster/1994'
    DSL_URL = 'https://www.milb.com/dominican-summer/roster/629'

    names = []
    for URL in [MLB_URL, AAA_URL, AA_URL, HighA_URL, A_URL, ACL_URL, DSL_URL]:
        level_names = scrape_roster(URL)
        for name in level_names:
            if name == 'Jose De':
                name = 'Jose De La Cruz'
            names.append(name)

    return names


