#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
GENERATION_DIR = BASE_DIR / "GenerationScripts"
LIGGGHTS_WRITER = BASE_DIR / "liggghtsWriter.py"


def as_list(value):
    if isinstance(value, list):
        return value
    return [value]


def sanitize(value):
    return (
        str(value)
        .replace("/", "_")
        .replace(" ", "_")
    )


def build_parameter_combinations(parameters):
    keys = list(parameters.keys())
    values = [as_list(parameters[key]) for key in keys]

    for combination in itertools.product(*values):
        yield dict(zip(keys, combination))


def build_algorithm_runs(algorithm_config):
    """
    Supports both:
      "parameters": {...}
    and:
      "generates": [
          {...},
          {...}
      ]

    Each generate block creates its own Cartesian product.
    """
    if "generates" in algorithm_config:
        generate_groups = algorithm_config["generates"]

    elif "parameters" in algorithm_config:
        # Backwards compatibility with older configs
        generate_groups = [
            algorithm_config["parameters"]
        ]

    else:
        raise ValueError(
            "Algorithm configuration must contain "
            "'parameters' or 'generates'"
        )

    runs = []

    for group_number, parameters in enumerate(
        generate_groups,
        start=1
    ):
        for combination in build_parameter_combinations(parameters):
            runs.append({
                "group": group_number,
                "parameters": combination
            })

    return runs


def build_output_name(algorithm_name, parameters):
    ignored_parameters = {
        "max_try",
        "plot-scaling",
        "tol_ov"
    }

    aliases = {
        "N_target": "N",
        "random_seed": "seed"
    }

    parts = [algorithm_name]

    for key, value in parameters.items():
        if key in ignored_parameters:
            continue

        key_name = aliases.get(key, key)
        parts.append(
            f"{key_name}_{sanitize(value)}"
        )

    return "_".join(parts)


def parameter_to_cli(command, key, value):
    if isinstance(value, bool):
        if value:
            command.append(f"--{key}")
    else:
        command.extend([
            f"--{key}",
            str(value)
        ])


def run_command(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print()
        print("ERROR:")
        print(" ".join(map(str, command)))

        if result.stdout.strip():
            print()
            print(result.stdout)

        if result.stderr.strip():
            print()
            print(result.stderr)

        raise subprocess.CalledProcessError(
            result.returncode,
            command
        )


def build_display_params(combination):
    display = []

    for key, value in combination.items():
        if key in ("N_target", "Np"):
            display.append(f"N={value}")

        elif key == "Df":
            display.append(f"Df={value}")

        elif key == "kf":
            display.append(f"kf={value}")

        elif key == "r_sigma_mult":
            display.append(f"r_sigma={value}")

        elif key == "random_seed":
            display.append(f"seed={value}")

    return "  ".join(display)


def generate_algorithm(
    algorithm_name,
    algorithm_config,
    output_root,
    liggghts_enabled,
    density
):
    if not algorithm_config.get("enabled", False):
        return 0

    script_name = algorithm_config["script"]
    script = GENERATION_DIR / script_name

    if not script.exists():
        raise FileNotFoundError(
            f"Generation script does not exist: {script}"
        )

    algorithm_output_dir = output_root / algorithm_name
    algorithm_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    sys_output_dir = algorithm_output_dir / "sys"

    if liggghts_enabled:
        sys_output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    runs = build_algorithm_runs(algorithm_config)

    print()
    print("=" * 70)
    print(f"Algorithm : {algorithm_name}")
    print(f"Runs      : {len(runs)}")
    print("=" * 70)

    generated = 0

    for run_number, run in enumerate(
        runs,
        start=1
    ):
        group_number = run["group"]
        combination = run["parameters"]

        output_name = build_output_name(
            algorithm_name,
            combination
        )

        csv_file = (
            algorithm_output_dir
            / f"{output_name}.csv"
        )

        display_params = build_display_params(
            combination
        )

        print(
            f"[{run_number}/{len(runs)}] "
            f"{algorithm_name} "
            f"(set {group_number})"
            + (
                f"  {display_params}"
                if display_params
                else ""
            )
        )

        command = [
            sys.executable,
            str(script)
        ]

        for key, value in combination.items():
            parameter_to_cli(
                command,
                key,
                value
            )

        command.extend([
            "--output",
            str(csv_file)
        ])

        run_command(command)
        print("      -> CSV written")

        if liggghts_enabled:
            sys_file = (
                sys_output_dir
                / f"{output_name}.sys"
            )

            liggghts_command = [
                sys.executable,
                str(LIGGGHTS_WRITER),
                str(csv_file),
                "--density",
                str(density),
                "--output",
                str(sys_file)
            ]

            run_command(
                liggghts_command
            )

            print("      -> SYS written")

        generated += 1

    return generated


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "config",
        type=str,
        help="JSON generation configuration"
    )

    args = parser.parse_args()

    config_file = Path(
        args.config
    ).resolve()

    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file does not exist: {config_file}"
        )

    with open(
        config_file,
        "r"
    ) as f:
        config = json.load(f)

    output_directory = config.get(
        "output_directory",
        "generated"
    )

    output_root = Path(output_directory)

    if not output_root.is_absolute():
        output_root = BASE_DIR / output_root

    output_root.mkdir(
        parents=True,
        exist_ok=True
    )

    liggghts_config = config.get(
        "liggghts",
        {}
    )

    liggghts_enabled = liggghts_config.get(
        "enabled",
        True
    )

    density = liggghts_config.get(
        "density",
        2.0
    )

    algorithms = config.get(
        "algorithms",
        {}
    )

    try:
        display_output = output_root.relative_to(
            BASE_DIR
        )
    except ValueError:
        display_output = output_root

    print()
    print("=" * 70)
    print("AUTOMATED AGGLOMERATE GENERATION")
    print("=" * 70)
    print(f"Config    : {config_file.name}")
    print(f"Output    : {display_output}")
    print(f"LIGGGHTS  : {liggghts_enabled}")
    print(f"Density   : {density}")
    print("=" * 70)

    total_generated = 0

    for algorithm_name, algorithm_config in algorithms.items():
        total_generated += generate_algorithm(
            algorithm_name,
            algorithm_config,
            output_root,
            liggghts_enabled,
            density
        )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)
    print(f"Generated : {total_generated}")
    print(f"Output    : {display_output}")
    print("=" * 70)


if __name__ == "__main__":
    main()
