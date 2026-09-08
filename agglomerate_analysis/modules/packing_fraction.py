#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 15:21:09 2026

Calculates the packing fraction based on the convex hull volume.

@author: sp00fer
"""

import numpy as np

from modules.convex_hull_volume import calculate_convex_hull


NAME = "packing fraction"

VERSION = "0.1"

DESCRIPTION = "Calculates the packing fraction based on the convex hull volume."


def calculate(agglomerate, n_points=8):

    # Calculate convex hull
    hull = calculate_convex_hull(
        agglomerate,
        n_points=n_points
    )

    hull_volume = hull.volume

    # Calculate total particle volume
    particle_volume = np.sum(
        (4.0 / 3.0)
        * np.pi
        * agglomerate.radii**3
    )

    # Calculate packing fraction
    packing_fraction = (
        particle_volume
        / hull_volume
    )

    return float(
        packing_fraction
    )