#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sun Apr 12 20:52:39 2026

@author: sp00feR

small visualization tool for plotting larger particle aggregates using pyvista instead of matplotlib for faster 3D Rendering
"""

import pandas as pd
import tkinter as tk
from tkinter import filedialog
import numpy as np
import pyvista as pv
import os
import re

#CONFIGURATION
particle_radius = 1.0
theta_res = 12
phi_res = 12
opacity = 1
colormap = "turbo"

# hide tk window
root = tk.Tk()
root.withdraw()

#open file dialog
datei_pfad = filedialog.askopenfilename(
    title="choose csv",
    filetypes=[("CSV-Files", "*.csv"), ("All files", "*.*")]
)

#open csv
if datei_pfad:
    df = pd.read_csv(datei_pfad)
    print("opened file:")
    print(df.head())
else:
    raise Exception("No File selected...")

#extract title from filename
dateiname = os.path.basename(datei_pfad)
dateiname_ohne_endung = os.path.splitext(dateiname)[0]

match = re.search(r"Df_([0-9.]+)_kf_([0-9.]+)_N_([0-9]+)", dateiname_ohne_endung)

if match:
    df_wert = match.group(1)
    kf_wert = match.group(2)
    n_wert = match.group(3)
    titel = f"Df = {df_wert}, kf = {kf_wert}, N = {n_wert}"
else:
    titel = dateiname_ohne_endung

#create numpy array
#PyVista only accepts Nx3 arrays for point coordinates
particles = df[["x", "y", "z"]].to_numpy(dtype=float)

#use radius column from csv if available
if "r" in df.columns:
    radii = df["r"].to_numpy(dtype=float)
else:
    radii = np.full(len(particles), particle_radius)

#radial coloring
center = particles.mean(axis=0)
dist = np.linalg.norm(particles - center, axis=1)

#display using pv
cloud = pv.PolyData(particles)
cloud["radius"] = radii
cloud["dist"] = dist

sphere = pv.Sphere(
    radius=1.0,
    theta_resolution=theta_res,
    phi_resolution=phi_res
)

glyphs = cloud.glyph(scale="radius", geom=sphere)

plotter = pv.Plotter()
plotter.set_background("white")

plotter.add_mesh(
    glyphs,
    scalars="dist",
    cmap=colormap,
    opacity=opacity,
    smooth_shading=True,
    specular=0.35,
    diffuse=0.8,
    ambient=0.25,
    show_scalar_bar=True,
    scalar_bar_args={
        "title": "distance from center",
        "vertical": True,
        "title_font_size": 14,
        "label_font_size": 12
    }
)

plotter.add_axes()
plotter.enable_eye_dome_lighting()
plotter.camera_position = "iso"

#plotter.add_text("Ringl, Urbassek N = 1000, r_sigma = 4 * r_particle", position="upper_edge", font_size=16)
plotter.add_text(titel, position="upper_edge", font_size=16, color="black")

plotter.show()