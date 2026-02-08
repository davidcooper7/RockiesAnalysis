import os, sys, json
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.table import Table
from matplotlib.patches import Circle
import numpy as np
sys.path.append('/home/dcooper/rockies/RockiesAnalysis')
from utils.analysis.savant import get_pitcher_home_away_movement, filter_df

pitch_full_names = json.load(open('/home/dcooper/rockies/RockiesAnalysis/utils/analysis/savant_pitch_names.json', 'r'))
pitch_colors = json.load(open('/home/dcooper/rockies/RockiesAnalysis/utils/analysis/savant_pitch_colors.json', 'r'))

def confidence_ellipse_params(x, y, n_std=1.25):
    """
    Returns ellipse parameters (width, height, angle, center)
    for a 2D confidence ellipse.
    """
    cov = np.cov(x, y)
    mean_x, mean_y = np.mean(x), np.mean(y)

    # Eigen decomposition
    eigenvals, eigenvecs = np.linalg.eigh(cov)

    # Sort largest → smallest
    order = eigenvals.argsort()[::-1]
    eigenvals = eigenvals[order]
    eigenvecs = eigenvecs[:, order]

    # Width and height of ellipse
    width = 2 * n_std * np.sqrt(eigenvals[0])
    height = 2 * n_std * np.sqrt(eigenvals[1])

    # Angle in degrees
    angle = np.degrees(np.arctan2(eigenvecs[1, 0], eigenvecs[0, 0]))

    return mean_x, mean_y, width, height, angle

from matplotlib.patches import Ellipse
def plot_pitch_ellipse(ax, x, y, facecolor, edgecolor, hatch=None, label=None, n_std=1.25, zorder=None):
    cx, cy, w, h, angle = confidence_ellipse_params(x, y, n_std)

    ellipse = Ellipse(
        (cx, cy),
        width=w,
        height=h,
        angle=angle,
        facecolor=facecolor,
        alpha=0.5,
        edgecolor=edgecolor,
        lw=2,
        label=label,
        hatch=hatch,
        zorder=zorder
    )

    ax.add_patch(ellipse)
    ax.scatter(cx, cy, s=12, color=edgecolor)


def plot_base(figsize=(6,6)):
    fig, ax = plt.subplots(figsize=figsize)

    # Plot cross hairs
    ax.vlines(0, -24 ,24, color='k', alpha=0.15)
    ax.hlines(0, -24 ,24, color='k', alpha=0.15)

    # Plot circles
    from matplotlib.patches import Circle
    circle_r = np.array([6, 12, 18, 24])
    circle_ls = np.array(['dashed', 'solid', 'dashed', 'solid'])
    for r, ls in zip(circle_r, circle_ls):
        circle = Circle((0,0), radius=r, facecolor='none', edgecolor='black', lw=1, linestyle=ls, alpha=0.15)
        ax.add_patch(circle)

    # Add labels
    ax.text(-7, -2,'6"', color='grey')
    ax.text(-13, -2,'12"', color='grey')
    ax.text(-19, -2,'18"', color='grey')
    ax.text(-25, -2,'24"', color='grey')
    ax.text(11, -2,'12"', color='grey')
    ax.text(23, -2,'24"', color='grey')
    ax.text(1, 11,'12"', color='grey')
    ax.text(1, 23,'24"', color='grey')
    ax.text(1, -11,'12"', color='grey')
    ax.text(1, -23,'24"', color='grey')

    return fig, ax

def _add_home_away_table(fig, ax):
    """
    Home/Away hatch table
    """
    # Initalize table
    from matplotlib.table import Table
    ax_table = fig.add_axes([0.675,0.3,0.175,0.08])
    ax_table.axis('off')
    table = Table(ax_table, bbox=[1,1,1,1])

    # Home
    cell = table.add_cell(0,0,width=0.1, height=0.1, facecolor=to_rgba('black', 0.15), edgecolor='black')
    cell.visible_edges = 'closed'
    cell = table.add_cell(0,1,width=0.15, height=0.1, text='Home')
    cell.visible_edges = 'open'

    # Away
    cell = table.add_cell(1,0,width=0.1, height=0.1, facecolor='white', edgecolor='black')
    cell.set_hatch('///')
    cell.visible_edges = 'closed'
    cell = table.add_cell(1,1,width=0.15, height=0.1, text='Away')
    cell.visible_edges = 'open'

    # Set font and add
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    ax_table.add_table(table)

    return fig, ax

def _add_pitch_type_table(fig, ax):
    """
    Pitch types table
    """
    # Initialize table
    ax_table = fig.add_axes([0.25,0.35,0.6,0.2])
    ax_table.axis('off')
    table = Table(ax_table, bbox=[1,1,1,1])
    
    # Add headers
    cell = table.add_cell(0,1,width=0.6, height=1, text='Pitch')
    cell.visible_edges = 'B'
    cell.get_text().set_ha("left")
    cell = table.add_cell(0,2,width=0.4, height=2, text='ΔBreak\n(in)')
    cell.visible_edges = 'B'
    cell.get_text().set_ha("left")
    cell = table.add_cell(0,3,width=0.6, height=2, text='Usage\n(Home : Away)')
    cell.visible_edges = 'B'
    cell.get_text().set_ha("left")

    return fig, ax, ax_table, table

def plot_pitcher_home_away_movement(last, first, year=2025, show: bool=True):
    """
    Plot pitcher home v away movement from savant
    """

    # Get playerid
    from utils.scraping.safe_playerid_lookup import savant_playerid_lookup
    playerid = savant_playerid_lookup(last, first)

    # Get pitch data from season
    from utils.scraping.savant import load_pitch_data
    pitch_data = load_pitch_data(year, year)

    # Get pitch data for player
    # from utils.analysis.savant import filter_df
    pitcher_df = filter_df(pitch_data, playerid=playerid, pitcher=True, pitcher_on_team='COL')

    # Get pitch split info 
    pitch_split_df, h_xy, aw_xy = get_pitcher_home_away_movement(pitcher_df)
    
    # Plot base 
    fig, ax = plot_base()

    # Add tables
    fig, ax = _add_home_away_table(fig, ax)
    fig, ax, ax_pitch_table, pitch_table = _add_pitch_type_table(fig, ax) 

    # Iterate through pitchers
    from matplotlib.colors import to_rgba
    for i, ((pitch, r), (phx, phy), (pawx, pawy)) in enumerate(zip(pitch_split_df.iterrows(), h_xy, aw_xy)):

        # Plot elipses 
        plot_pitch_ellipse(ax, pawx, pawy, facecolor='white', edgecolor=to_rgba(pitch_colors[pitch]), hatch='///', zorder=10)
        plot_pitch_ellipse(ax, phx, phy, facecolor=to_rgba(pitch_colors[pitch]), edgecolor=to_rgba(pitch_colors[pitch]), zorder=20)

        # Add to legend table
        cell = pitch_table.add_cell(i+1, 0, width=0.2, height=1.5, facecolor=(to_rgba(pitch_colors[pitch]), 0.5), edgecolor=to_rgba(pitch_colors[pitch]))
        cell.visible_edges = 'closed'
        cell = pitch_table.add_cell(i+1, 1, width=0.6, height=1.5, text=pitch)
        cell.visible_edges = 'open'
        cell.get_text().set_ha("left")
        cell = pitch_table.add_cell(i+1, 2, width=0.4, height=1.5, text=f'{-r['ΔBreak']:.1f}')
        cell.visible_edges = 'open'
        cell.get_text().set_ha("left")
        cell = pitch_table.add_cell(i+1, 3, width=0.4, height=1.5, text=f'{100*r['Home Usage']:.0f}% : {100*r['Away Usage']:.0f}%')
        cell.visible_edges = 'open'
        cell.get_text().set_ha("left")

    # Finish table
    pitch_table.auto_set_font_size(False)
    pitch_table.set_fontsize(9)
    ax_pitch_table.add_table(pitch_table)

    # Set limits
    ax.set_xlim(-30, 30)
    ax.set_ylim(-30, 30)
    ax.set_aspect("equal")
    
    # Turn ticks off
    ax.set_xticks([], [])
    ax.set_yticks([], [])
    
    # Title
    ax.set_title(f'{first} {last} {year}\nMovement Profile Home/Road')
    
    # Convert into circle
    clip_circle = Circle(
        (0, 0),        # center
        radius=25,     # match axis limits
        transform=ax.transData
    )
    for artist in ax.get_children():
        artist.set_clip_path(clip_circle)

    # Show, if specified
    if show:
        plt.show()
    
    return fig, ax, pitch_split_df

    