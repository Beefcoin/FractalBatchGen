#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import itertools
import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
GENERATION_DIR = BASE_DIR / "GenerationScripts"
LIGGGHTS_WRITER = BASE_DIR / "liggghtsWriter.py"
ANALYSIS_SCRIPT = BASE_DIR / "agglomerate_analysis" / "main.py"


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
    values = [
        as_list(parameters[key])
        for key in keys
    ]

    for combination in itertools.product(*values):
        yield dict(
            zip(keys, combination)
        )


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
        generate_groups = algorithm_config[
            "generates"
        ]

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
        for combination in build_parameter_combinations(
            parameters
        ):
            runs.append({
                "group": group_number,
                "parameters": combination
            })

    return runs


def build_output_name(
    algorithm_name,
    parameters
):
    ignored_parameters = {
        "max_try",
        "plot-scaling",
        "tol_ov"
    }

    aliases = {
        "N_target": "N",
        "random_seed": "seed"
    }

    parts = [
        algorithm_name
    ]

    for key, value in parameters.items():
        if key in ignored_parameters:
            continue

        key_name = aliases.get(
            key,
            key
        )

        parts.append(
            f"{key_name}_{sanitize(value)}"
        )

    return "_".join(parts)


def parameter_to_cli(
    command,
    key,
    value
):
    if isinstance(value, bool):
        if value:
            command.append(
                f"--{key}"
            )

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

    # Successful execution
    if result.returncode == 0:
        return result

    # Expected generation failure:
    # the requested parameter combination could not be generated.
    if result.returncode == 69:
        return result

    # Unexpected error:
    # show full subprocess output for debugging.
    print()
    print("ERROR:")
    print(
        " ".join(
            map(str, command)
        )
    )

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
        if key in (
            "N_target",
            "Np"
        ):
            display.append(
                f"N={value}"
            )

        elif key == "Df":
            display.append(
                f"Df={value}"
            )

        elif key == "kf":
            display.append(
                f"kf={value}"
            )

        elif key == "r_sigma_mult":
            display.append(
                f"r_sigma={value}"
            )

        elif key == "random_seed":
            display.append(
                f"seed={value}"
            )

    return "  ".join(display)


# =============================================================
# Analysis
# =============================================================

def normalize_metadata(
    algorithm_name,
    parameters
):
    """
    Normalize parameter names used by different generation
    algorithms so that they can be stored in one common
    analysis table.
    """
    aliases = {
        "N_target": "N",
        "Np": "N",
        "random_seed": "seed"
    }

    metadata = {
        "algorithm": algorithm_name
    }

    for key, value in parameters.items():
        normalized_key = aliases.get(
            key,
            key
        )

        metadata[
            normalized_key
        ] = value

    return metadata


def read_analysis_result(result):
    """
    Read the JSON result returned by
    agglomerate_analysis/main.py.
    """
    stdout = result.stdout.strip()

    if not stdout:
        raise ValueError(
            "Analysis returned no output"
        )

    try:
        return json.loads(
            stdout
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Could not parse analysis output as JSON:\n"
            f"{stdout}"
        ) from exc


def load_existing_analysis_rows(
    csv_file
):
    """
    Load an existing analysis CSV.

    This is required because different generation algorithms
    may contain different input parameters. If a new column
    appears, the existing table is rewritten with the extended
    header.
    """
    if not csv_file.exists():
        return [], []

    with open(
        csv_file,
        "r",
        newline=""
    ) as f:
        reader = csv.DictReader(
            f
        )

        fieldnames = (
            reader.fieldnames
            if reader.fieldnames
            else []
        )

        rows = list(
            reader
        )

    return fieldnames, rows


def append_analysis_result(
    analysis_csv,
    metadata,
    results,
    input_file
):
    """
    Add one generated agglomerate and its analysis results
    to the common analysis table.
    """
    row = {}

    # Generation parameters
    row.update(
        metadata
    )

    # Morphological analysis results
    row.update(
        results
    )

    # Original generated CSV for traceability
    row["input_file"] = (
        input_file.name
    )

    existing_fields, existing_rows = (
        load_existing_analysis_rows(
            analysis_csv
        )
    )

    fieldnames = list(
        existing_fields
    )

    # Add newly appearing parameters or analysis properties
    # to the CSV header automatically.
    for key in row.keys():
        if key not in fieldnames:
            fieldnames.append(
                key
            )

    existing_rows.append(
        row
    )

    analysis_csv.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        analysis_csv,
        "w",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for existing_row in existing_rows:
            writer.writerow(
                existing_row
            )


def run_analysis(
    csv_file,
    analysis_csv,
    algorithm_name,
    parameters
):
    """
    Run the standalone agglomerate analysis program and
    store its results together with the generation parameters.
    """
    if not ANALYSIS_SCRIPT.exists():
        raise FileNotFoundError(
            f"Analysis script does not exist: "
            f"{ANALYSIS_SCRIPT}"
        )

    command = [
        sys.executable,
        str(ANALYSIS_SCRIPT),
        str(csv_file)
    ]

    result = run_command(
        command
    )

    analysis_results = (
        read_analysis_result(
            result
        )
    )

    metadata = (
        normalize_metadata(
            algorithm_name,
            parameters
        )
    )

    append_analysis_result(
        analysis_csv,
        metadata,
        analysis_results,
        csv_file
    )


# =============================================================
# Generation
# =============================================================

def generate_algorithm(
    algorithm_name,
    algorithm_config,
    output_root,
    liggghts_enabled,
    density,
    analysis_enabled,
    analysis_csv
):
    if not algorithm_config.get(
        "enabled",
        False
    ):
        return 0

    script_name = algorithm_config[
        "script"
    ]

    script = (
        GENERATION_DIR
        / script_name
    )

    if not script.exists():
        raise FileNotFoundError(
            f"Generation script does not exist: {script}"
        )

    # ---------------------------------------------------------
    # Algorithm output directory
    # ---------------------------------------------------------

    algorithm_output_dir = (
        output_root
        / algorithm_name
    )

    algorithm_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # ---------------------------------------------------------
    # SYS output directory
    # ---------------------------------------------------------

    sys_output_dir = (
        algorithm_output_dir
        / "sys"
    )

    if liggghts_enabled:
        sys_output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    # ---------------------------------------------------------
    # Build generation runs
    # ---------------------------------------------------------

    runs = build_algorithm_runs(
        algorithm_config
    )

    print()
    print("=" * 70)
    print(
        f"Algorithm : {algorithm_name}"
    )
    print(
        f"Runs      : {len(runs)}"
    )
    print("=" * 70)

    #counters for failures / generates
    generated = 0
    failed = 0

    for run_number, run in enumerate(
        runs,
        start=1
    ):
        group_number = run[
            "group"
        ]

        combination = run[
            "parameters"
        ]

        output_name = (
            build_output_name(
                algorithm_name,
                combination
            )
        )

        csv_file = (
            algorithm_output_dir
            / f"{output_name}.csv"
        )

        display_params = (
            build_display_params(
                combination
            )
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

        # -----------------------------------------------------
        # Generate agglomerate
        # -----------------------------------------------------

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

        generation_result = run_command(
            command
        )

        if generation_result.returncode == 69:
            print(
                "      -> Generation failed"
            )
            print(
                "         Check generation parameters."
            )
            failed += 1
            continue

        print(
            "      -> CSV written"
        )

        # -----------------------------------------------------
        # Generate LIGGGHTS SYS
        # -----------------------------------------------------

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

            print(
                "      -> SYS written"
            )

        # -----------------------------------------------------
        # Analyze agglomerate
        # -----------------------------------------------------

        if analysis_enabled:
            run_analysis(
                csv_file,
                analysis_csv,
                algorithm_name,
                combination
            )

            print(
                "      -> Analysis written"
            )

        generated += 1

    return generated, failed


# =============================================================
# Main
# =============================================================

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
            f"Config file does not exist: "
            f"{config_file}"
        )

    with open(
        config_file,
        "r"
    ) as f:
        config = json.load(
            f
        )

    # ---------------------------------------------------------
    # Output configuration
    # ---------------------------------------------------------

    output_directory = config.get(
        "output_directory",
        "generated"
    )

    output_root = Path(
        output_directory
    )

    if not output_root.is_absolute():
        output_root = (
            BASE_DIR
            / output_root
        )

    output_root.mkdir(
        parents=True,
        exist_ok=True
    )

    # ---------------------------------------------------------
    # LIGGGHTS configuration
    # ---------------------------------------------------------

    liggghts_config = config.get(
        "liggghts",
        {}
    )

    liggghts_enabled = (
        liggghts_config.get(
            "enabled",
            True
        )
    )

    density = liggghts_config.get(
        "density",
        2.0
    )

    # ---------------------------------------------------------
    # Analysis configuration
    # ---------------------------------------------------------

    analysis_config = config.get(
        "analysis",
        {}
    )

    analysis_enabled = (
        analysis_config.get(
            "enabled",
            False
        )
    )

    analysis_output_dir = (
        output_root
        / "analysis"
    )

    analysis_csv = (
        analysis_output_dir
        / "analysis.csv"
    )

    if analysis_enabled:
        analysis_output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    # ---------------------------------------------------------
    # Algorithms
    # ---------------------------------------------------------

    algorithms = config.get(
        "algorithms",
        {}
    )

    try:
        display_output = (
            output_root.relative_to(
                BASE_DIR
            )
        )

    except ValueError:
        display_output = (
            output_root
        )

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "AUTOMATED AGGLOMERATE GENERATION"
    )
    print("=" * 70)
    print(
        f"Config    : {config_file.name}"
    )
    print(
        f"Output    : {display_output}"
    )
    print(
        f"LIGGGHTS  : {liggghts_enabled}"
    )
    print(
        f"Density   : {density}"
    )
    print(
        f"Analysis  : {analysis_enabled}"
    )

    if analysis_enabled:
        try:
            display_analysis = (
                analysis_csv.relative_to(
                    BASE_DIR
                )
            )
        except ValueError:
            display_analysis = (
                analysis_csv
            )

        print(
            f"Analysis CSV: {display_analysis}"
        )

    print("=" * 70)

    # ---------------------------------------------------------
    # Run algorithms
    # ---------------------------------------------------------

    total_generated = 0
    total_failed = 0

    for (
        algorithm_name,
        algorithm_config
    ) in algorithms.items():

        generated, failed = generate_algorithm(
            algorithm_name,
            algorithm_config,
            output_root,
            liggghts_enabled,
            density,
            analysis_enabled,
            analysis_csv
        )

        total_generated += generated
        total_failed += failed

    # ---------------------------------------------------------
    # Finished
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)
    print(
        f"Generated : {total_generated}"
    )
    print(
        f"Failed    : {total_failed}"
    )
    print(
        f"Output    : {display_output}"
    )

    if analysis_enabled:
        print(
            f"Analysis  : {display_analysis}"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()