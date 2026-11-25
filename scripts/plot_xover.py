#!/usr/bin/env python3
"""Histogram + latitude scatter of the cross-over SLA differences (cf. thesis Fig. 28)."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

csv_path = sys.argv[1] if len(sys.argv) > 1 else "xover_finder.csv"
out_png = sys.argv[2] if len(sys.argv) > 2 else "dsla.png"

d = np.genfromtxt(csv_path, delimiter=",", names=True)
dsla, lat = np.atleast_1d(d["dsla"]), np.atleast_1d(d["lat"])

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(7, 7),
                               gridspec_kw={"height_ratios": [1, 2]})
ax1.hist(dsla, bins=100, color="tab:blue")
ax1.set_ylabel("Frequency")
ax1.set_title("SLA cross-over difference (CryoSat-2 - Jason-2)")
ax1.text(0.02, 0.8, f"Mean = {dsla.mean():.3f} m\nSigma = {dsla.std():.3f} m\nn = {dsla.size}",
         transform=ax1.transAxes, bbox=dict(fc="w", ec="k"))
ax2.scatter(dsla, lat, s=2, c="k")
ax2.set_xlabel("SLA cross-over difference (m)")
ax2.set_ylabel("Latitude (deg)")
fig.tight_layout()
fig.savefig(out_png, dpi=150)
print("saved", out_png)
