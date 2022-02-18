import pprint
from typing import Callable, Dict, List, Union

import pandas as pd


class Model:
    def __init__(self, names: List[str]):
        """Base class for models of outputs as function of inputs.

        Args:
            names: names of the modeled outputs
        """
        for name in names:
            if not isinstance(name, str):
                TypeError("Model: names must be a list of strings.")
        self.names = list(names)

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        """Evaluate the objective values for a given DataFrame."""
        raise NotImplementedError

    def to_config(self) -> None:
        """Return a json-serializable dictionary of the objective."""
        pass  # non-serializable models should be ommited without raising an error


class LinearModel(Model):
    """Model to compute an output as a linear/affine function of the inputs."""

    def __init__(self, names: List[str], coefficients, offset: float = 0):
        super().__init__(names)
        if len(names) > 1:
            raise ValueError("LinearModel can only describe a single output.")
        self.coefficients = coefficients
        self.offset = offset

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        y = df.to_numpy() @ self.coefficients + self.offset
        return pd.DataFrame(y, columns=self.names)

    def __repr__(self):
        return f"LinearModel({self.names}, coefficients={self.coefficients}, offset={self.offset})"

    def to_config(self) -> Dict:
        return dict(
            type="linear-model",
            names=self.names,
            coefficients=self.coefficients,
            offset=self.offset,
        )


class CustomModel(Model):
    """Custom model for arbitrary functions."""

    def __init__(self, names: List[str], f: Callable):
        super().__init__(names)
        self.f = f

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.f(df)

    def __repr__(self):
        return f"CustomModel({self.names}, f={self.f})"


class Models:
    """Container for models."""

    def __init__(self, models: Union[List[Model], List[Dict]]):
        _models = []
        for m in models:
            if isinstance(m, Model):
                _models.append(m)
            else:
                _models.append(make_model(**m))
        self.models = _models

    def __call__(self, y: pd.DataFrame) -> pd.DataFrame:
        return pd.concat([model(y) for model in self.models], axis=1)

    def __repr__(self):
        return "Models(\n" + pprint.pformat(self.models) + "\n)"

    def __iter__(self):
        return iter(self.models)

    def __len__(self):
        return len(self.models)

    def __getitem__(self, i: int) -> Model:
        return self.models[i]

    @property
    def names(self):
        names = []
        for model in self.models:
            names += model.names
        return names

    def to_config(self) -> List[Dict]:
        return [
            model.to_config() for model in self.models if model.to_config() is not None
        ]


def make_model(type, **kwargs):
    t = type.lower()
    if t == "linear-model":
        return LinearModel(**kwargs)
    raise ValueError(f"Unknown model type: {t}.")
