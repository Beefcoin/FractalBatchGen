from dataclasses import dataclass
import numpy as np


@dataclass
class Agglomerate:
    positions: np.ndarray
    radii: np.ndarray


def load_csv(filename: str) -> Agglomerate:
    data = np.loadtxt(filename, delimiter=",", skiprows=1)

    positions = data[:, 0:3]
    radii = data[:, 3]

    return Agglomerate(
        positions=positions,
        radii=radii
    )