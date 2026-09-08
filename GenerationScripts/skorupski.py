#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Sun Apr 12 11:36:48 2026

@author: sp00feR

There are a lot of optimization strategies that can still be applied to this code but this will only be needed for agglomerates exceeding 10k particles i think.

Based on this: 
Krzysztof Skorupski, Janusz Mroczka, Thomas Wriedt, Norbert Riefler,
A fast and accurate implementation of tunable algorithms used for generation of fractal-like aggregate models,
Physica A: Statistical Mechanics and its Applications,
Volume 404,
2014,
Pages 106-117,
ISSN 0378-4371,
https://doi.org/10.1016/j.physa.2014.02.072.
(https://www.sciencedirect.com/science/article/pii/S0378437114001812)
Abstract: In many branches of science experiments are expensive, require specialist equipment or are very time consuming. Studying the light scattering phenomenon by fractal aggregates can serve as an example. Light scattering simulations can overcome these problems and provide us with theoretical, additional data which complete our study. For this reason a fractal-like aggregate model as well as fast aggregation codes are needed. Until now various computer models, that try to mimic the physics behind this phenomenon, have been developed. However, their implementations are mostly based on a trial-and-error procedure. Such approach is very time consuming and the morphological parameters of resulting aggregates are not exact because the postconditions (e.g. the position error) cannot be very strict. In this paper we present a very fast and accurate implementation of a tunable aggregation algorithm based on the work of Filippov et al. (2000). Randomization is reduced to its necessary minimum (our technique can be more than 1000 times faster than standard algorithms) and the position of a new particle, or a cluster, is calculated with algebraic methods. Therefore, the postconditions can be extremely strict and the resulting errors negligible (e.g. the position error can be recognized as non-existent). In our paper two different methods, which are based on the particle–cluster (PC) and the cluster–cluster (CC) aggregation processes, are presented.
Keywords: Fractal aggregates; Particle–cluster aggregation; Cluster–cluster aggregation
"""

import numpy as np
import math
import pyvista as pv
import argparse


""" #CONFIGURATION
particle_radius = 1.0
random_seed = 420
kf = 0.4
Df = 3
N_target = 1000
max_try = 1000 """

#read cmdline arg
parser = argparse.ArgumentParser()

parser.add_argument("--particle_radius", type=float, required=True)
parser.add_argument("--random_seed", type=int, required=True)
parser.add_argument("--kf", type=float, required=True)
parser.add_argument("--Df", type=float, required=True)
parser.add_argument("--N_target", type=int, required=True)
parser.add_argument("--max_try", type=int, required=True)
parser.add_argument("--output", type=str, required=True)
parser.add_argument("--plot-scaling", action="store_true")

args = parser.parse_args()

particle_radius = args.particle_radius
random_seed = args.random_seed
kf = args.kf
Df = args.Df
N_target = args.N_target
max_try = args.max_try
output_file = args.output
plot_scaling = args.plot_scaling

print("=" * 40)
print("CONFIG DEBUG")
print("=" * 40)
print(f"particle_radius : {particle_radius:>10.4f}")
print(f"random_seed     : {random_seed:>10}")
print(f"kf              : {kf:>10.4f}")
print(f"Df              : {Df:>10.4f}")
print(f"N_target        : {N_target:>10}")
print(f"max_try         : {max_try:>10}")
print(f"output_file     : {output_file}")
print(f"plot_scaling    : {plot_scaling}")
print("=" * 40)

#basic vector normalization method
def normalize(v):
    return v / np.linalg.norm(v)

#this is used for creating a vector perpendicular to v
def createPerpendicularVector(v):
    if abs(v[0]) < 0.9:
        helper = np.array([1.0, 0.0, 0.0])
    else:
        helper = np.array([0.0, 1.0, 0.0])

    perpendicular = np.cross(v, helper)
    perpendicular = normalize(perpendicular)
    return perpendicular

#this is used for rotating a vector around an axis using Rodrigues rotation formula
def rotateVector(v, axis, angle):
    axis = normalize(axis)
    rotated_v = (
        v * math.cos(angle)
        + np.cross(axis, v) * math.sin(angle)
        + axis * np.dot(axis, v) * (1 - math.cos(angle))
    )
    return rotated_v

#this is used for checking if the new particle overlaps with any particle in LA
def checkOverlap(new_particle, LA):
    #use a small tolerance to prevent floating point rounding errors from treating contacting particles as overlapping
    diameter = 2.0 * particle_radius
    tol = 1e-12 * diameter

    for particle in LA:
        #calculate distance between new particle and particle q from candidate list
        d = np.linalg.norm(new_particle - particle)

        #check if particles overlap
        if d < diameter - tol:
            return True

    return False


#this is Eq. 16, Marsaglia Method
def randomSpherePoint():
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

#this is used for calculating the geometric center of an aggregate according to Eq. 17a
def calculateCenter(particles):
    sum_P = 0

    for q in range(len(particles)):
        sum_P += particles[q]

    C_Np = sum_P / len(particles)
    return C_Np

#this is used for updating the geometric center incrementally according to Eq. 17b
def calculateCenterInc(center, N_old, new_particle):
    C_new = (center * N_old + new_particle) / (N_old + 1)
    return C_new

#this creates a list of candidates for the addition of a new particle "the distance between the centers of the particles must be equal or greater than 2rp"
def createCandidateList(particles, center, gamma):
    LA = []

    diameter = 2.0 * particle_radius
    tol = 1e-12 * diameter

    for q in range(len(particles)):
        #calculate distance of particle q to geometric center
        d = np.linalg.norm(particles[q] - center)

        #use tolerance to avoid platform dependent decisions close to the candidate boundary
        if d >= gamma - diameter - tol:
            LA.append(particles[q])

    return LA

#this calculates alpha according to Appendix A3  Eq. 18
def calculateAlpha(center, reference_particle, gamma):
    CB = reference_particle - center
    CB_length = np.linalg.norm(CB)
    AB = 2 * particle_radius

    cos_alpha = (gamma**2 + CB_length**2 - AB**2) / (2 * gamma * CB_length)

    alpha = math.acos(cos_alpha)
    return alpha

#this creates a new particle based on center, gamma and a ref particle
def createNewParticle(center, gamma, reference_particle):
    #horrible geometrical shit here
    #we are searchging for a point A, where A is on the Particle around C with r = gamma && |AB| = 2rp
    #- calculate alpha according to Appendix A3  Eq. 18
    alpha = calculateAlpha(center, reference_particle, gamma)
    #- create vector from center to ref_particle
    CB = reference_particle - center
    
    #- create perpendicular unit vector 
    CB_unit = normalize(CB)
    perpendicular = createPerpendicularVector(CB_unit)
    
    #- create gamma vector with angle alpha to CB
    gamma_vector = gamma * (math.cos(alpha) * CB_unit + math.sin(alpha) * perpendicular)
    
    #- choose rabdom rotation angle beta
    beta = np.random.uniform(0, 2 * math.pi)
    
    #- rotate gamma vector around CB axis
    gamma_vector_rotated = rotateVector(gamma_vector, CB_unit, beta)
    
    #- calculate new particle position
    new_particle = center + gamma_vector_rotated
    
    return new_particle


#this creates the fractal scaling plot shown in Fig. 8 and estimates Df from the slope
def plotFractalScaling(particles):
    import matplotlib.pyplot as plt

    N_values = []
    Rg_over_rp = []

    #calculate Rg incrementally for every aggregation step
    center = np.zeros(3, dtype=float)
    sum_squared_distances = 0.0

    for i, particle in enumerate(particles, start=1):
        delta = particle - center
        center = center + delta / i
        delta2 = particle - center
        sum_squared_distances = sum_squared_distances + np.dot(delta, delta2)

        if i >= 2:
            Rg = math.sqrt(sum_squared_distances / i)
            N_values.append(i)
            Rg_over_rp.append(Rg / particle_radius)

    N_values = np.array(N_values, dtype=float)
    Rg_over_rp = np.array(Rg_over_rp, dtype=float)

    #fit ln(Np) = ln(kf) + Df * ln(Rg/rp), Df is the slope
    slope, intercept = np.polyfit(np.log(Rg_over_rp), np.log(N_values), 1)
    Df_approx = slope
    kf_approx = math.exp(intercept)

    print("Approximated fractal dimension Df:", Df_approx)
    print("Approximated fractal prefactor kf:", kf_approx)

    plt.figure(figsize=(7, 5))
    plt.loglog(Rg_over_rp, N_values, linewidth=1.5, label="PC")
    plt.xlabel(r"$R_g/r_p$")
    plt.ylabel(r"$N_p$")
    plt.text(0.67, 0.52, rf"$D_f \approx {Df_approx:.4f}$", transform=plt.gca().transAxes, fontsize=13)
    plt.grid(True, which="both", linestyle=":", linewidth=0.6)
    plt.legend()
    plt.tight_layout()

    plot_name = "fractal_scaling_Df_" + str(Df) + "_kf_" + str(kf) + "_N_" + str(N_target) + ".png"
    plt.savefig(plot_name, dpi=300)
    plt.show()

    return Df_approx, kf_approx

#set a fixed random seed for reproducibility
np.random.seed(random_seed)

#1. create two contacting particles
particles = []

# first particle at geometry origin 0,0,0
p1 = np.array([0.0, 0.0, 0.0])
particles.append(p1)

#add second particle in direct contact
d = randomSpherePoint()
p2 = p1 + d * (2 * particle_radius)
particles.append(p2)

#debug
print(particles)
print("Distance:", np.linalg.norm(particles[1] - particles[0]))


#main loop until target number of particles is reached
while len(particles) < N_target:

    #2. calculate geometric center of the cluster only for the first 2, after we do it incrementally
    if(len(particles) == 2):
        center = calculateCenter(particles)

    #3. calculate gamma according to Eq. 2 -> radius where the new particle has to be 
    Np = len(particles) + 1

    gamma_squared = (
        ((Np**2 * particle_radius**2) / (Np - 1)) * ((Np / kf) ** (2 / Df))
        - ((Np * particle_radius**2) / (Np - 1))
        - (Np * particle_radius**2) * (((Np - 1) / kf) ** (2 / Df))
    )

    gamma = math.sqrt(gamma_squared)

    #print("Current particles:", len(particles))
    #print("Center:", center)
    #print("Gamma:", gamma)
    
    #4. create candidate list LA
    LA = createCandidateList(particles, center, gamma)
    #print(LA)
    #5. try to find one valid new particle
    particle_added = False
    tr = 0
    while particle_added == False:
       tr += 1
       #choose a random reference particle (is this right?? idk i am brain damaged)
       reference_particle = LA[np.random.randint(len(LA))]
       #print(reference_particle)
   
       #6. create new particle
       new_particle = createNewParticle(center, gamma, reference_particle)

       #7. check overlap
       overlap = checkOverlap(new_particle, LA)
       #8. append particle if no overlap exists
       if overlap == False:
            N_old = len(particles)
            particles.append(new_particle)
            center = calculateCenterInc(center, N_old, new_particle)
            particle_added = True
            print("Particle added (", len(particles), "/", N_target, ")")

       if tr > max_try:
           print("Generation failed... Check generation parameters.")
           sys.exit(69)
           

if plot_scaling:
    plotFractalScaling(particles)


#save as CSV
#add particle radius to the output particle list
particles_out = np.column_stack((particles, np.full(len(particles), particle_radius)))
#export to csv 
np.savetxt(output_file, particles_out, delimiter=",")

