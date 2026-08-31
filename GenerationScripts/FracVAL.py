#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This is a really cheap py2f Wrapper for FracVAL, 
# I implemented a new F90 Wrapper and changed all parameters to allocatable (DATA etc) 


import numpy as np
import argparse
import sys
from pathlib import Path

#add FracVALFortran subfolder to python module search path
script_dir = Path(__file__).resolve().parent
fracval_dir = script_dir / "FracVALFortran"
sys.path.insert(0, str(fracval_dir))

import fracval
from FileWriter import writeCSV, writeVTP

#read cmdline args
parser = argparse.ArgumentParser()

parser.add_argument("--Np", type=int, required=True)
parser.add_argument("--Df", type=float, required=True)
parser.add_argument("--kf", type=float, required=True)
parser.add_argument("--Dp_geo", type=float, required=True)
parser.add_argument("--Dp_gsd", type=float, required=True)
parser.add_argument("--tol_ov", type=float, required=True)
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--random_seed", type=int, required=True)

args = parser.parse_args()

Np = args.Np #number of particles   
Df = args.Df #fractal Dimension
kf = args.kf #fractal Prefactor
Dp_geo = args.Dp_geo #particle Diameter
Dp_gsd = args.Dp_gsd #standard dev. for particle Diameter (1 -> monodisperse)    
tol_ov = args.tol_ov #overlapping tolerance (1e-06 is default for FracVAL)
random_seed = args.random_seed
output_file = args.output

#Debug for the Wrapper
print("FracVAL import location:", fracval.__file__)
print("available names:", dir(fracval))

def debug_config():
    print("\n=== FracVAL Configuration ===")
    print(f"Np              : {Np}")
    print(f"Df              : {Df}")
    print(f"kf              : {kf}")
    print(f"Dp_geo          : {Dp_geo}")
    print(f"Dp_gsd          : {Dp_gsd}")
    print(f"tol_ov          : {tol_ov}")
    print(f"output          : {output_file}")
    print(f"seed            : {random_seed}")
    print("=============================")


#fancy param print
debug_config()

#call my epic wrapper here
print("\nGenerating CCA Aggregate using Fortran FracVAL, depending on N this might take a while...\n")
coords, diam, failed = fracval.fracval_wrapper.run_fracval(
    Np,
    Df, 
    kf, 
    Dp_geo,
    Dp_gsd, 
    tol_ov,
    random_seed
)

if failed:
    raise Exception("Generation failed... Check Generation Parameters!")

#save CSV
fileNameCSV = output_file
radii = diam / 2
writeCSV(coords,radii,fileNameCSV)    
