# Automated Agglomerate Generation

Batch-generation workflow for creating fractal agglomerates with
different generation algorithms and exporting them as CSV and LIGGGHTS
`.sys` files.

## Requirements

A dedicated Conda environment is recommended.

### Python

-   Python \>= 3.12
-   NumPy
-   Matplotlib
-   PyVista
-   Meson
-   Ninja

Use the provided `environment.yml` to create and activate the environment:

``` bash
conda env create -f environment.yml
conda activate agglomerate-generation
```

### FracVAL / F2PY

FracVAL is written in Fortran and exposed to Python through a NumPy F2PY
extension. Building the extension additionally requires:

-   NumPy / F2PY
-   GNU Fortran compiler (`gfortran`)
-   C compiler / build tools
-   Meson
-   Ninja

On Ubuntu/Debian, the required system compilers can be installed with:

``` bash
sudo apt install build-essential gfortran
```

Check that the required tools are available:

``` bash
gcc --version
gfortran --version
python -m numpy.f2py --help
meson --version
ninja --version
```

## Structure

``` text
AutomatedGeneration/
├── generate.sh
├── batch_generate.py
├── liggghtsWriter.py
├── README.md
├── config/
│   ├── README.md
│   ├── genTest_skorupski.json
│   ├── genTest_urbassek.json
│   └── genTest_FracVAL.json
└── GenerationScripts/
    ├── skorupski.py
    ├── urbassek3d.py
    ├── FracVAL.py
    └── FracVALFortran/
```

## Building FracVAL

FracVAL has to be compiled for the Python version used by the active
environment.

Activate the Conda environment first:

``` bash
conda activate agglomerate-generation
```

Then build the F2PY extension from the FracVAL source directory:

``` bash
cd GenerationScripts/FracVALFortran

python -m numpy.f2py -c \
  Ctes.f90 random.f90 RAND_SAMPLE.f90 a_Random_PP.f90 \
  PCA_cca.f90 PCA_Subclusters_module.f90 \
  CCA_module.f90 fracval_wrapper.f90 \
  -m fracval \
  only: run_fracval init_ctes :
```

This creates a Python extension similar to:

``` text
fracval.cpython-312-x86_64-linux-gnu.so
```

Keep the compiled module inside `GenerationScripts/FracVALFortran/`.

> **Note:** The F2PY module is Python-version dependent. Rebuild it
> after changing the Python version or environment if the existing
> module is incompatible.

The build can be tested from the project root with:

``` bash
python -c "import sys; sys.path.insert(0, 'GenerationScripts/FracVALFortran'); import fracval; print(fracval.__file__)"
```

## Running

Make the launcher executable once:

``` bash
chmod +x generate.sh
```

Run one of the included test configurations:

``` bash
./generate.sh config/genTest_skorupski.json
./generate.sh config/genTest_urbassek.json
./generate.sh config/genTest_FracVAL.json
```

The batch runner reads the selected JSON configuration and generates the
Cartesian product of all list-valued parameters. Scalar parameters
remain constant for all corresponding runs.

If LIGGGHTS export is enabled in the configuration, every generated CSV
is automatically passed to `liggghtsWriter.py`, producing a matching
`.sys` file with the configured particle density.

Generated files are written to the `output_directory` specified in the
JSON configuration.

## Configuration

Generation parameters, parameter sweeps, random seeds, output
directories, LIGGGHTS export, and particle density are controlled
through the JSON configuration files.

See [`config/README.md`](configs/README.md) for the configuration
format and examples.
