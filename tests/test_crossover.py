import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from xover_finder import crossover


def make_tracks(offset=0.047):
    # Two straight tracks crossing at (lat, lon) = (10.0, 20.0), ~0.02 deg spacing
    t = np.linspace(-0.03, 0.03, 7)
    cryo = np.c_[10.0 + 3.0 * t, 20.0 + t, 0.10 + 0.5 * t]
    jas = np.c_[10.0 - 1.0 * t, 20.0 + t, 0.10 - offset + 0.2 * t]
    return cryo, jas


def test_position_and_difference():
    cryo, jas = make_tracks()
    lat, lon, sla_c, sla_j, dsla, *_ = crossover(cryo, jas)
    assert abs(lat - 10.0) < 1e-6 and abs(lon - 20.0) < 1e-6
    assert abs(dsla - 0.047) < 1e-6


def test_distant_tracks_rejected():
    cryo, jas = make_tracks()
    jas[:, 0] += 5.0
    assert crossover(cryo, jas) is None
