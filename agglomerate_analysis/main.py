#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Tue Sep  8 09:41:06 2026

This is an implementation for the customizable agglomerate analysis. It is based on a module registry so new analysis methods can be easily added in the future.

@author: sp00fer
"""

import argparse
import json
from pathlib import Path

from agglomerate import load_csv
from registry import ModuleRegistry

#add new modules here:
from modules import convex_hull_volume
from modules import porosity


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Analyze morphological properties of an agglomerate."
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="CSV file containing the agglomerate."
    )

    return parser.parse_args()


def register_modules(registry):
    # -------------------------
    # Register analysis modules
    # -------------------------

    # Register analysis modules here:
    registry.register(
        convex_hull_volume,
        n_points=8
    )

    registry.register(
        porosity
    )



def main():
    args = parse_arguments()

    input_file = Path(args.input_file)

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {input_file}"
        )

    #load agglomerate
    agglomerate = load_csv(
        input_file
    )

    
    #create module registry
    registry = ModuleRegistry()

    #register modules
    register_modules(registry)

    #run all modules
    results = registry.run_all(
        agglomerate
    )

    # Output results as JSON for batch_generate.py
    print(
        json.dumps(results)
    )


if __name__ == "__main__":
    main()