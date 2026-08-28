#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 09:09:24 2026

@author: sp00feR

This implementation becomes slow for larger particle counts because, at each growth step, phi_i is recomputed for all existing particles. Each phi_i
evaluation requires iterating over the full particle list again to count neighbors within r_sigma, and each overlap check for a new candidate also
scans all existing particle. Maybe it can be optimized...

Based on: 
Christian Ringl, Herbert M. Urbassek,
A simple algorithm for constructing fractal aggregates with pre-determined fractal dimension,
Computer Physics Communications,
Volume 184, Issue 7,
2013,
Pages 1683-1685,
ISSN 0010-4655,
https://doi.org/10.1016/j.cpc.2013.02.012.
(https://www.sciencedirect.com/science/article/pii/S0010465513000696)
Abstract: We present an algorithm which allows to construct fractal aggregates, composed of equal-sized grains, with pre-determined fractal dimension. The basic idea consists in growing the aggregates by adding grains at that position where the local filling factor is smallest. We then show that there exists an approximately linear relationship between the fractal dimension and the detector radius by which the local filling factor is determined. Fractal dimensions between 1.7 and 3.0 have been realized as examples for aggregates containing 102–104 grains.
Keywords: Fractal aggregates; Granular mechanics; Porous clusters
"""

import math
import random
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
import argparse


""" #CONFIGURATION
N_target = 1000 #number of particles in the fractal network
max_try = 200 #number of crys for step 3
r_particle = 1 #particle radius
r_sigma_mult = 10
seed = 420
"""

#read cmdline arg
parser = argparse.ArgumentParser()

parser.add_argument("--N_target", type=int, required=True)
parser.add_argument("--max_try", type=int, required=True)
parser.add_argument("--particle_radius", type=float, required=True)
parser.add_argument("--r_sigma_mult", type=float, required=True)
parser.add_argument("--random_seed", type=int, required=True)
parser.add_argument("--output", type=str, required=True)

args = parser.parse_args()

N_target = args.N_target #number of particles in the fractal network
max_try = args.max_try #number of trys for step 3
r_particle = args.particle_radius #particle radius
r_sigma_mult = args.r_sigma_mult
r_sigma = r_sigma_mult * r_particle #'detection radius'
seed = args.random_seed
output_file = args.output

print("=" * 40)
print("CONFIG DEBUG")
print("=" * 40)
print(f"N_target        : {N_target:>10}")
print(f"max_try         : {max_try:>10}")
print(f"particle_radius : {r_particle:>10.4f}")
print(f"r_sigma_mult    : {r_sigma_mult:>10.4f}")
print(f"random_seed     : {seed:>10}")
print(f"output_file     : {output_file:>10}")
print("=" * 40)

#set a fixed random seed for reproducibility
random.seed(seed)
np.random.seed(seed)

#simple distance function for 2 points
def distance(a, b):
    return math.sqrt(
        (a[0] - b[0]) ** 2 +
        (a[1] - b[1]) ** 2 +
        (a[2] - b[2]) ** 2
    )


#checking function for overlap when generating particles
def checkOverlap(candidate, existing_particles, min_dist):
    for p in existing_particles:
        if distance(candidate, p) < min_dist:
            return True
    return False


#count neighbors in radius
def countNeighborsSigma(particle, all_particles, radius):
    count = 0
    for other in all_particles:
        if other is particle:
            continue
        #if there is another particle inside our detection radius -> increase count
        if distance(particle, other) <= radius:
            count += 1
    return count

#calculate phi_i according to Ringl 2013 Eq.3
def calculatePhiI(particle, all_particles):
    N_sigma = countNeighborsSigma(particle, all_particles, r_sigma)
    numerator = N_sigma * 4 * math.pi * ((r_particle ** 3) / 3)
    denominator = 4 * math.pi * ((r_sigma ** 3) / 3)
    return numerator / denominator

#this is Eq. 16, Marsaglia Method (i took this from my other implementation of Skorupski algorithm because its nice)
def randomUnitVector3d():
    while True:
        #create two random numbers from -1 to 1 
        x1 = np.random.uniform(-1, 1)
        x2 = np.random.uniform(-1, 1)

        #check wether criterium x1² + x2² < 1
        c = x1**2 + x2**2

        if c < 1:
            #create R vector and leave
            R = np.array([
                2*x1*np.sqrt(1-c),
                2*x2*np.sqrt(1-c),
                1 - 2*c
            ])
            return R

#iterate over N
# for each N:
    #1. calculate phi_i for each grain
        #1.count number of particles in r_sigma from each particle
        #2.phi_i = (N_sigma * 4*pi * (r_particle^3)/3) / (4*pi*((r_sigma^3)/3)
    #2. select grain with lowest phi_i (if not unique, choose with random seed)
    #3. attach a grain to it at a random direction (seed)
    #->limit number of trys
    #-> if max number reached go back to step 2 and choose a different grain



#particel array
particles = [(0.0, 0.0, 0.0)]

#main loop until target number of particles is reached
while len(particles) < N_target:
    attached = False

    #we calculate phi_i for every grain
    phi_values = []
    for p in particles:
        phi_values.append((p, calculatePhiI(p, particles)))

    #we find our minimum phi_i and add it to the candidate list, there might be more than one
    min_phi = min(phi for _, phi in phi_values)
    candidates = [p for p, phi in phi_values if abs(phi - min_phi) == 0] #maybe we should check with a small epsilon bc float shit but it works for now

    #randomly order our canditates seed based so we can pick randomly but reproducibly
    random.shuffle(candidates)

    #try to attach the candidate
    for seed in candidates:
        #simple timout otherwise this might get stuck here
        for _ in range(max_try):
            direction = randomUnitVector3d()
            new_particle = (
                seed[0] + 2 * r_particle * direction[0],
                seed[1] + 2 * r_particle * direction[1],
                seed[2] + 2 * r_particle * direction[2],
            )
        #check wether overlap occurs with other particles in the agglomerate
            if not checkOverlap(new_particle, particles, 2 * r_particle):
                particles.append(new_particle)
                attached = True
                print("Attached particle (", len(particles), "/", N_target, ")")
                break

        if attached:
            break

    if not attached:
        raise  Exception("Could not attach particle @ N = ", len(particles), " Check Generation Settings!")



#save as CSV
#add particle radius to the output particle list
particles_out = np.column_stack((particles, np.full(len(particles), r_particle)))
np.savetxt(output_file, particles_out, delimiter=",")
