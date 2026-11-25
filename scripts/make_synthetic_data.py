#!/usr/bin/env python3
"""
Generate a SYNTHETIC cross-over CSV (same columns as xover_finder.py) so the
plotting scripts and the example notebook can be run without RADS data.
The numbers are random and have no scientific meaning.
"""
import sys
import numpy as np

out = sys.argv[1] if len(sys.argv) > 1 else "synthetic_xovers.csv"
rng = np.random.default_rng(42)
n = 30000
lat = np.degrees(np.arcsin(rng.uniform(-np.sin(np.radians(66)), np.sin(np.radians(66)), n)))
lon = rng.uniform(-180, 180, n)
# ocean variability grows poleward of ~30 deg; noise follows it
scale = 0.05 + 0.08 * (np.abs(lat) > 30)
sla_j = rng.normal(0.02, scale)
sla_c = 0.8 * sla_j + rng.normal(-0.009, 0.045, n)
header = "lat,lon,sla_cryosat,sla_jason,dsla,ssr_cryosat,r2_cryosat,ssr_jason,r2_jason"
rows = np.c_[lat, lon, sla_c, sla_j, sla_c - sla_j, np.zeros(n), np.ones(n), np.zeros(n), np.ones(n)]
np.savetxt(out, rows, delimiter=",", header=header, comments="")
print("wrote", out)
