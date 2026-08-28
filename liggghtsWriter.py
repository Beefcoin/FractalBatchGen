#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import argparse
from pathlib import Path


ATOM_TYPES = 2
BOND_TYPES = 0
ANGLE_TYPES = 0
#bounds in x,y,z
BOUNDS = [(-100, 100), (-100, 100), (-100, 100)]


def load_particles(input_file):
    with open(input_file, "r") as f:
        first_line = f.readline().strip()

    try:
        [float(x) for x in first_line.split(",")]
        skiprows = 0
    except ValueError:
        skiprows = 1

    particles = np.loadtxt(
        input_file,
        delimiter=",",
        skiprows=skiprows
    )

    if particles.ndim == 1:
        particles = particles.reshape(1, -1)

    return particles

def writeLightsAgglomerateFile(outFile, particles, density):
    print("Writing agglomerate file to ", outFile, " length = ", particles.size)
    print()
    
    with open(outFile, "w") as f:
        
        ##Create Header
        #-> write "LIGGGHTS Description"
        f.write("LIGGGHTS Description\n\n")
        #-> write {particles.lenght} atoms
        f.write(f"{len(particles)} atoms\n")
        #-> write {atomTypes = 2} atom types
        f.write(f"{ATOM_TYPES} atom types\n")
        #-> write {bondTypes = 0} bond types
        f.write(f"{BOND_TYPES} bond types\n")
        #-> write {angleTypes = 0} angle types
        f.write(f"{ANGLE_TYPES} angle types\n\n")
        
        ##Write bounds
        f.write(f"{BOUNDS[0][0]}e00 {BOUNDS[0][1]}e00  xlo xhi\n")
        f.write(f"{BOUNDS[0][0]}e00 {BOUNDS[0][1]}e00  ylo yhi\n")
        f.write(f"{BOUNDS[0][0]}e00 {BOUNDS[0][1]}e00  zlo zhi\n\n")
        
        ##Write actual Atom content with indent
        f.write("Atoms\n\n")
        atomType = 1
        for atom_id, p in enumerate(particles, start=1):
            indent = " " * (6-len(str(atom_id)))
            diameter = 2 * p[3]
            f.write(indent + f"{atom_id}  {atomType} {diameter: .12E} {density: .12E} {p[0]: .12E} {p[1]: .12E} {p[2]: .12E}\n")
            
        f.write("\n")
            
        ##Write Velocities (all to 0 for now)
        f.write("Velocities\n\n")
        velocity = 0.0
        for atom_id, p in enumerate(particles, start=1):
            indent = " " * (6-len(str(atom_id)))
            f.write(indent + f"{atom_id} {velocity: .1f} {velocity: .1f} {velocity: .1f} {velocity: .1f} {velocity: .1f} {velocity: .1f}\n")
        
        #i dont know if this is needed, but the original file has it
        f.write("\n")


parser = argparse.ArgumentParser()

parser.add_argument("input", type=str)
parser.add_argument("--density", type=float, default=2.0)
parser.add_argument(
    "--output",
    type=str,
    default=None,
    help="Optional output .sys file"
)

args = parser.parse_args()

input_file = Path(args.input)

if not input_file.exists():
    raise FileNotFoundError(f"Input file does not exist: {input_file}")

particles = load_particles(input_file)

if particles.ndim == 1:
    particles = particles.reshape(1, -1)

if particles.shape[1] < 4:
    raise ValueError("CSV file must contain at least four columns: x, y, z, radius")

if args.output is not None:
    output_file = Path(args.output)
else:
    output_file = input_file.with_suffix(".sys")

output_file.parent.mkdir(
    parents=True,
    exist_ok=True
)

writeLightsAgglomerateFile(output_file, particles, args.density)