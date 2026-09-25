"""Cost-to-Orbit: a sourced dataset of launch price per kilogram to LEO.

The dataset is the product; everything else here exists to keep it honest.

    from cost_to_orbit import load_dataset
    ds = load_dataset()
    ds.cheapest(basis="dedicated_list")
"""

from cost_to_orbit.dataset import Dataset, load_dataset
from cost_to_orbit.models import Deflator, FrontierPoint, Vehicle

__version__ = "1.0.0"

__all__ = [
    "Dataset",
    "Deflator",
    "FrontierPoint",
    "Vehicle",
    "load_dataset",
    "__version__",
]
