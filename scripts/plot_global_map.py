#!/usr/bin/env python3
"""
Global map of cross-over values (cf. thesis Figs. 25, 27, 29).

Usage:
    python scripts/plot_global_map.py xover_finder.csv map_dsla.png
    python scripts/plot_global_map.py xover_finder.csv map_cryo.png --variable sla_cryosat --title "CryoSat-2 SLA"

Variables: dsla (default), sla_cryosat, sla_jason.
Coastlines are drawn if Cartopy is installed (pip install cartopy);
otherwise a plain lon/lat scatter is produced.
"""
import argparse

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# red - orange - yellow - green - yellow - orange - red, as in the thesis maps
THESIS_CMAP = LinearSegmentedColormap.from_list(
    "thesis", ["#e8262a", "#f58a3c", "#f5c84c", "#e3ef5a", "#a6e05c",
               "#e3ef5a", "#f5c84c", "#f58a3c", "#e8262a"])


def plot_map(lon, lat, values, title="", vlim=0.5, size=2.0, ax=None, cmap=THESIS_CMAP):
    """Scatter `values` (m) on a lon/lat map, saturating the colour scale at +/- vlim."""
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        if ax is None:
            fig = plt.figure(figsize=(13, 6.5))
            ax = plt.axes(projection=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, facecolor="0.92", zorder=0)
        ax.coastlines(linewidth=0.5, zorder=3)
        ax.set_global()
        kw = {"transform": ccrs.PlateCarree()}
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="gray", alpha=0.6)
        gl.top_labels = gl.right_labels = False
    except ImportError:
        if ax is None:
            fig, ax = plt.subplots(figsize=(13, 6.5))
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_xlabel("Longitude (deg)")
        ax.set_ylabel("Latitude (deg)")
        ax.grid(lw=0.3, alpha=0.6)
        ax.set_aspect("equal")
        kw = {}
    sc = ax.scatter(lon, lat, c=values, s=size, cmap=cmap, vmin=-vlim, vmax=vlim,
                    linewidths=0, zorder=2, **kw)
    cb = plt.colorbar(sc, ax=ax, orientation="horizontal", pad=0.15, fraction=0.04, extend="both")
    cb.set_label("m")
    ax.set_title(title)
    return ax


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?", default="xover_finder.csv")
    ap.add_argument("out", nargs="?", default="map.png")
    ap.add_argument("--variable", default="dsla", choices=["dsla", "sla_cryosat", "sla_jason"])
    ap.add_argument("--title", default=None)
    ap.add_argument("--vlim", type=float, default=0.5, help="colour scale limit in metres (default 0.5)")
    ap.add_argument("--size", type=float, default=2.0, help="marker size")
    args = ap.parse_args()

    d = np.genfromtxt(args.csv, delimiter=",", names=True)
    title = args.title or {"dsla": "SLA cross-over difference (CryoSat-2 - Jason-2)",
                           "sla_cryosat": "CryoSat-2 SLA at cross-over",
                           "sla_jason": "Jason-2 SLA at cross-over"}[args.variable]
    plot_map(np.atleast_1d(d["lon"]), np.atleast_1d(d["lat"]), np.atleast_1d(d[args.variable]),
             title=title, vlim=args.vlim, size=args.size)
    plt.savefig(args.out, dpi=200, bbox_inches="tight")
    print("saved", args.out)


if __name__ == "__main__":
    main()
