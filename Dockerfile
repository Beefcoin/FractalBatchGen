FROM continuumio/miniconda3@sha256:f37f8c7db26ae7ec0098df530e96c9cde139026b9faf3914800d1522c47a49b1

WORKDIR /app

# ------------------------------------------------------------
# System dependencies
# ------------------------------------------------------------

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gfortran \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# Conda environment
# ------------------------------------------------------------

COPY conda-linux-64.lock /app/conda-linux-64.lock

RUN conda create \
    --name agglomerate-generation \
    --file /app/conda-linux-64.lock \
    --yes && \
    conda clean -afy


# Use project environment by default
ENV PATH=/opt/conda/envs/agglomerate-generation/bin:$PATH


# ------------------------------------------------------------
# Copy project
# ------------------------------------------------------------

COPY . /app


# ------------------------------------------------------------
# Build FracVAL
# ------------------------------------------------------------

WORKDIR /app/GenerationScripts/FracVALFortran

RUN python -m numpy.f2py -c \
    Ctes.f90 \
    random.f90 \
    RAND_SAMPLE.f90 \
    a_Random_PP.f90 \
    PCA_cca.f90 \
    PCA_Subclusters_module.f90 \
    CCA_module.f90 \
    fracval_wrapper.f90 \
    -m fracval \
    only: run_fracval init_ctes :


# ------------------------------------------------------------
# Return to project root
# ------------------------------------------------------------

WORKDIR /app


# Make launcher executable
RUN chmod +x generate.sh


CMD ["bash"]
