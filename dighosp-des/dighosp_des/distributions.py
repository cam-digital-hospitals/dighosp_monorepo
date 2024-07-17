"""Defines dataclasses for probability distributions."""

from typing import Callable, Literal, Self, Union

import pydantic as pyd
import salabim as sim


class DistributionInfo(pyd.BaseModel):
    """Information describing a three-point random distributions for task durations."""

    type: Literal['Constant', 'Triangular', 'PERT'] = pyd.Field(
        title='Distribution type',
    )
    """The type of the distribution, one of 'Constant', 'Triangular', or 'PERT'."""

    low: pyd.NonNegativeFloat = pyd.Field(title='Lower bound')
    mode: pyd.NonNegativeFloat = pyd.Field(title='Most likely value')
    high: pyd.NonNegativeFloat = pyd.Field(title='Upper bound')

    time_unit: Literal['s', 'm', 'h'] = pyd.Field(
        title='Time unit',
    )
    """The time unit of the distribution, i.e. seconds, minutes, or hours. Represented by the
    first letter; the validator will accept any string starting with 's', 'm', or 'h'."""

    @pyd.field_validator('time_unit', mode='before')
    @classmethod
    def _first_letter(cls, time_unit_str: str) -> str:
        """Take only the first letter from a time-unit string.

        For simplicity, only the first character of time-unit strings are checked, i.e.
        "hours", "hour", and "hxar" are identical.
        """
        assert time_unit_str[0] in ['s', 'm', 'h'], 'Invalid time unit string'
        return time_unit_str[0]

    @pyd.model_validator(mode='after')
    def _enforce_ordering(self) -> Self:
        """Ensure that the the ``low``, ``mode`` and ``high`` parameters of the distribution
        are in non-decreasing order."""
        # Constant case
        if self.type == 'Constant':
            return __class__.model_construct(
                type='Constant', low=self.mode, mode=self.mode, high=self.mode,
                time_unit=self.time_unit
            )
        # Other cases
        assert self.mode >= self.low, 'Failed requirement: mode >= low'
        assert self.high >= self.mode, 'Failed requirement: high >= mode'
        return self


class IntDistributionInfo(pyd.BaseModel):
    """Information describing a discretised three-point random distribution.
    The underlying continuous distribution is constructed with parameters
    `(low - 0.5, mode, high + 0.5)`.
    """

    type: Literal['Constant', 'IntTriangular', 'IntPERT'] = pyd.Field(
        title='Distribution type',
    )
    """The type of the distribution, one of 'Constant', 'IntTriangular', or 'IntPERT'."""

    low: pyd.NonNegativeInt = pyd.Field(title='Lower bound')
    mode: pyd.NonNegativeInt = pyd.Field(title='Most likely value')
    high: pyd.NonNegativeInt = pyd.Field(title='Upper bound')

    @pyd.model_validator(mode='after')
    def _enforce_ordering(self) -> Self:
        """Ensure that the the ``low``, ``mode`` and ``high`` parameters of the distribution
        are in non-decreasing order."""
        # Constant case
        if self.type == 'Constant':
            return __class__.model_construct(
                type='Constant', low=self.mode, mode=self.mode, high=self.mode)
        # Other cases
        assert self.mode >= self.low, 'Failed requirement: mode >= low'
        assert self.high >= self.mode, 'Failed requirement: high >= mode'
        return self


# OVERRIDE SOME SALABIM DISTRIBUTIONS

class Constant(sim.Constant):
    """Constant distribution."""

    def __repr__(self):
        return f'Constant({self._value}, time_unit={self.time_unit})'


class Tri(sim.Triangular):
    """Triangular distribution."""

    # Reorder parameters
    def __init__(
            self,
            low: float,
            mode: float | None = None,
            high: float | None = None,
            time_unit: str | None = None,
            randomstream=None,
            env: sim.Environment | None = None
    ) -> None:
        super().__init__(low, high, mode, time_unit, randomstream, env)

    def __repr__(self) -> str:
        return f"Triangular(low={self._low}, mode={self._mode}, high={self._high}, "\
            f"time_unit={self.time_unit})"


# Note that we only inherit from sim.Triangular for convienience;
# the PERT distribution is *not* a special case of the triangular distribution.
class PERT(sim.Triangular):
    """PERT distribution.

    A three-point distribution with more probability mass around the mode than the
    triangular distribution.  The mean of the distribution is
    `(_low + _shape * _mode + _high) / (_shape + 2)`.
    By default, `_shape = 4`.
    """

    def __init__(
        self,
        low: float,
        mode: float | None = None,
        high: float | None = None,
        time_unit: str | None = None,
        randomstream=None,
        env: sim.Environment | None = None,
    ) -> None:
        super().__init__(low, high, mode, time_unit, randomstream, env)
        self._shape = 4

        self._range = high - low
        self._alpha = 1 + self._shape * (mode - low) / self._range
        self._beta = 1 + self._shape * (high - mode) / self._range

        self._mean = (low + self._shape * mode + high) / (self._shape + 2)

    def __repr__(self) -> str:
        return f"PERT(low={self._low}, mode={self._mode}, high={self._high}, "\
            f"shape={self._shape}, time_unit={self.time_unit})"

    def print_info(self, as_str: bool = False, file: sim.TextIO | None = None) -> str:
        """ Print info about the distribution."""
        result = []
        result.append("PERT " + hex(id(self)))
        result.append("  low=" + str(self._low) + " " + self.time_unit)
        result.append("  high=" + str(self._high) + " " + self.time_unit)
        result.append("  mode=" + str(self._mode) + " " + self.time_unit)
        result.append("  shape=" + str(self._shape))
        result.append("  randomstream=" + hex(id(self.randomstream)))
        return sim.return_or_print(result, as_str, file)

    def sample(self) -> float:
        beta = self.randomstream.betavariate
        val = self._low + beta(self._alpha, self._beta) * self._range
        return val * self.time_unit_factor

    def mean(self) -> float:
        return self._mean * self.time_unit_factor


Distribution = Union[Constant, Tri, PERT]
"""A continuous distribution (constant, triangular, or PERT)."""


# DISCRETIZED DISTRIBUTIONS
class IntPERT:
    """Discretized PERT distribution."""

    def __init__(
        self,
        low: int,
        mode: int,
        high: int,
        randomstream=None,
        env: sim.Environment | None = None
    ):
        self.low = low
        self.mode = mode
        self.high = high
        self.pert = PERT(low-mode-0.5, 0, high-mode+0.5, randomstream=randomstream, env=env)
        """Underlying continuous PERT distribution, i.e. `PERT(low-mode-0.5, 0, high-mode+0.5)`."""

    def sample(self) -> int:
        """Sample the distribution."""
        return self()

    def __call__(self) -> int:
        return int(self.pert.sample()) + self.mode  # Round towards 0, then add the mode

    def __repr__(self) -> str:
        return f'IntPERT({self.low}, {self.mode}, {self.high})'


class IntTri:
    """Discretized Triangular distribution."""

    def __init__(
        self,
        low: int,
        mode: int,
        high: int,
        randomstream=None,
        env: sim.Environment | None = None
    ):
        self.low = low
        self.mode = mode
        self.high = high
        self.tri = Tri(low-mode-0.5, 0, high-mode+0.5, randomstream=randomstream, env=env)
        """Underlying continuous Tri distribution, i.e. `Tri(low-mode-0.5, 0, high-mode+0.5)`."""

    def sample(self) -> int:
        """Sample the distribution."""
        return self()

    def __call__(self) -> int:
        # Round towards 0 and add the mode
        return int(self.tri.sample()) + self.mode

    def __repr__(self) -> str:
        return f'IntPERT({self.low}, {self.mode}, {self.high})'


class IntConstant(sim.Constant):
    """Alias of sim.Constant for integers."""
    value: int

    def __init__(
        self, value: int, randomstream=None, env: sim.Environment = None
    ):
        super().__init__(value, None, randomstream, env)

    sample: Callable[[Self], int]
    __call__: Callable[[Self], int]


IntDistribution = Union[IntConstant, IntTri, IntPERT]
"""A discrete distribution (integer-constant, integer-triangular, or integer-PERT)."""
