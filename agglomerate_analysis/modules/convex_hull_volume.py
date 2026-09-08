import numpy as np
from scipy.spatial import ConvexHull

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 14:41:06 2026

Calculates convex hull volume based on an implementation by Ali Khalifa.

@author: sp00fer
"""

NAME = "convex hull volume"

VERSION = "0.1"

DESCRIPTION = "Calculates the convex hull volume of the agglomerate."

def calculate_convex_hull(agglomerate, n_points=8):

    positions = agglomerate.positions
    radii = agglomerate.radii

    # Generate surface points for convex hull calculation
    phi = np.linspace(
        0,
        np.pi,
        n_points
    )

    theta = np.linspace(
        0,
        2 * np.pi,
        n_points
    )

    phi, theta = np.meshgrid(
        phi,
        theta
    )

    # Generate surface points for all particles at once
    x = (
        positions[:, 0][:, None, None]
        + radii[:, None, None]
        * np.sin(phi)
        * np.cos(theta)
    )

    y = (
        positions[:, 1][:, None, None]
        + radii[:, None, None]
        * np.sin(phi)
        * np.sin(theta)
    )

    z = (
        positions[:, 2][:, None, None]
        + radii[:, None, None]
        * np.cos(phi)
    )

    # Combine all surface points
    points = np.column_stack([
        x.ravel(),
        y.ravel(),
        z.ravel()
    ])

    # Calculate convex hull
    hull = ConvexHull(
        points
    )

    return hull


def calculate(agglomerate, n_points=8):

    hull = calculate_convex_hull(
        agglomerate,
        n_points=n_points
    )

    return float(
        hull.volume
    )