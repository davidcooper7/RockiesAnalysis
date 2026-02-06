import numpy as np
import matplotlib.pyplot as plt

# Methods to plot spray chart
def draw_field(ax, r=415):
    theta = np.linspace(-np.pi/4, np.pi/4, 200)
    ax.plot(r*np.sin(theta), r*np.cos(theta), color='black', lw=1)
    ax.plot(154*np.sin(theta), 154*np.cos(theta), color='black', lw=1)
    ax.plot([0, -r/np.sqrt(2)], [0, r/np.sqrt(2)], color='black', lw=1)
    ax.plot([0, r/np.sqrt(2)], [0, r/np.sqrt(2)], color='black', lw=1)
    ax.scatter(0, 0, color='black', s=20)  # home plate

    return ax

def draw_wedge(ax, range: tuple=(-45,45), val=1, norm_factor=1, r=415):
    from matplotlib.patches import Wedge

    theta1 = 90 - range[0] 
    theta2 = 90 - range[1]
    alpha = np.abs(val) / norm_factor
    if val > 0:
        color = 'red'
    else:
        color = 'blue'
    
    wedge = Wedge(
        center=(0,0),
        r=r,
        theta1=theta2,
        theta2=theta1,
        facecolor=color,
        alpha=alpha
    )
    ax.add_patch(wedge)
    return ax

def savant_to_field_xy(hc_x, hc_y):
    # Recenter at home plate
    x = hc_x - 125.0
    y = 199.0 - hc_y   # flip y-axis

    # Scale pixels → feet
    scale = 2.5
    return x * scale, y * scale
