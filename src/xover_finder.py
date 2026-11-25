#!/usr/bin/env python3
"""
Dual-satellite cross-over finder for CryoSat-2 and Jason-2 (RADS .asc files).

MSc project: Validation of CryoSat-2 satellite altimeter data over the ocean
Author:      Pablo Garcia Garcia (UCL, MSc Hydrographic Surveying, 2014)
Supervisor:  Prof. Marek Ziebart

Python 3 port of the original Python 2.7 script. The algorithm is unchanged:

  1. Estimate the cross-over with a closest-point search (cKD-tree).
  2. Re-estimate the cross-over position as the intersection of two straight
     lines fitted by least squares through the 4 nearest points of each track.
  3. Fit a cubic polynomial through the 4 SLA values of each track, evaluate
     both at the cross-over longitude and difference them:
         dSLA = SLA_cryosat - SLA_jason

Input files are RADS ASCII passes. Column 0 is ignored; columns 1, 2, 3 must be
latitude, longitude and sea level anomaly (SLA).
"""
import argparse
import csv
import fnmatch
import itertools
import os
import time
from functools import lru_cache

import numpy as np
from scipy import spatial

MAX_DIST_DEG = 0.06  # reject pass pairs whose closest points are further apart
BBOX_MARGIN = MAX_DIST_DEG

HEADER = [
    "lat", "lon", "sla_cryosat", "sla_jason", "dsla",
    "ssr_cryosat", "r2_cryosat", "ssr_jason", "r2_jason",
]


def _fit_line(lon, lat):
    """Least-squares line lat = m*lon + c. Returns m, c, sum of squared residuals, R^2."""
    A = np.vstack([lon, np.ones(len(lon))]).T
    (m, c), res, *_ = np.linalg.lstsq(A, lat, rcond=None)
    ssr = float(res[0]) if res.size else float(np.sum((lat - (m * lon + c)) ** 2))
    denom = lat.size * lat.var()
    r2 = float(1 - ssr / denom) if denom > 0 else float("nan")
    return m, c, ssr, r2


def crossover(cryo, jas, max_dist=MAX_DIST_DEG):
    """
    Compute the cross-over between one CryoSat-2 pass and one Jason-2 pass.

    cryo, jas : (N, 3) arrays with columns [lat, lon, sla].
    Returns a tuple matching HEADER, or None if the passes do not cross.
    """
    cryo_xy, jas_xy = cryo[:, :2], jas[:, :2]
    if len(cryo) < 4 or len(jas) < 4:
        return None

    # 1. closest-point estimate
    cryo_tree = spatial.cKDTree(cryo_xy)
    dists, idx = cryo_tree.query(jas_xy)
    j = int(np.argmin(dists))
    if dists[j] >= max_dist:
        return None
    seed = cryo_xy[idx[j]]

    # 2. four nearest points on each track around the seed -> two linear fits
    ic = cryo_tree.query(seed, k=4)[1]
    ij = spatial.cKDTree(jas_xy).query(seed, k=4)[1]
    m_c, c_c, ssr_c, r2_c = _fit_line(cryo_xy[ic, 1], cryo_xy[ic, 0])
    m_j, c_j, ssr_j, r2_j = _fit_line(jas_xy[ij, 1], jas_xy[ij, 0])
    if m_c == m_j:  # parallel tracks
        return None
    lon_x = (c_j - c_c) / (m_c - m_j)
    lat_x = m_c * lon_x + c_c

    # 3. cubic through the 4 SLA points of each track, evaluated at the cross-over
    sla_c = np.polyval(np.polyfit(cryo[ic, 1], cryo[ic, 2], 3), lon_x)
    sla_j = np.polyval(np.polyfit(jas[ij, 1], jas[ij, 2], 3), lon_x)

    return (lat_x, lon_x, sla_c, sla_j, sla_c - sla_j, ssr_c, r2_c, ssr_j, r2_j)


def find_files(root, pattern, max_pass=None):
    """Walk `root` for RADS pass files matching `pattern`; optionally limit pass number."""
    out = []
    for dirpath, _, names in os.walk(root):
        for name in fnmatch.filter(names, pattern):
            if max_pass is not None and not (1 <= int(name[3:7]) <= max_pass):
                continue
            out.append(os.path.join(dirpath, name))
    return sorted(out)


@lru_cache(maxsize=None)
def load_pass(path):
    arr = np.genfromtxt(path, usecols=(1, 2, 3), comments="#")
    arr = np.atleast_2d(arr)
    return arr[~np.isnan(arr).any(axis=1)]


def bboxes_overlap(a, b, margin=BBOX_MARGIN):
    """Cheap exact prefilter: points closer than `margin` require overlapping boxes."""
    return not (
        a[:, 0].max() + margin < b[:, 0].min() or b[:, 0].max() + margin < a[:, 0].min()
        or a[:, 1].max() + margin < b[:, 1].min() or b[:, 1].max() + margin < a[:, 1].min()
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data_dir", help="directory containing RADS .asc pass files (searched recursively)")
    ap.add_argument("-o", "--output", default="xover_finder.csv")
    ap.add_argument("--cryo-pattern", default="c2p0[0-9][0-9][0-9]c029*.asc",
                    help="glob for CryoSat-2 passes (default: cycle 029)")
    ap.add_argument("--jason-pattern", default="j2p0[0-9][0-9][0-9]c145*.asc",
                    help="glob for Jason-2 passes (default: cycle 145)")
    ap.add_argument("--max-pass", type=int, default=210,
                    help="highest CryoSat-2 pass number to use; limits the time lag between "
                         "satellites to <10 days (default: 210)")
    args = ap.parse_args()

    t0 = time.time()
    cryo_files = find_files(args.data_dir, args.cryo_pattern, args.max_pass)
    jas_files = find_files(args.data_dir, args.jason_pattern)
    print(f"{len(cryo_files)} CryoSat-2 passes, {len(jas_files)} Jason-2 passes")

    n = 0
    with open(args.output, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)
        for cf, jf in itertools.product(cryo_files, jas_files):
            c, j = load_pass(cf), load_pass(jf)
            if len(c) < 4 or len(j) < 4 or not bboxes_overlap(c, j):
                continue
            row = crossover(c, j)
            if row is not None:
                writer.writerow(row)
                n += 1
    print(f"{n} cross-overs written to {args.output} in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
