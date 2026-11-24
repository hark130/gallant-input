"""Describe a frequency-hopping system: its channels, its hop pattern, and how they match up.

ChannelPlan:  Channel numbers and their center frequencies.  Resolves a measured frequency to
              the nearest channel (a hard decision, like a slicer) and reports the residual.
HopPattern:   The (cyclic) sequence of channel numbers the transmitter hops through.  Aligns an
              observed channel sequence against itself.
FhssProfile:  One container holding a ChannelPlan and the HopPattern that uses it.

ChannelPlan and HopPattern stand alone: a plan is useful without hopping (e.g., any channelized
signal), and FhssProfile only checks that they agree.
"""

# Standard Imports
from dataclasses import dataclass
from typing import Mapping, Sequence, Tuple
# Third Party Imports
import numpy as np
# Local Imports


@dataclass(frozen=True)
class ChannelMatch:
    """One measured frequency, resolved to the nearest channel."""

    channel: int | None  # Nearest channel number (None if farther than max_residual_hz)
    channel_freq: float  # That channel's center frequency (Hz)
    residual_hz: float   # Measured minus channel_freq (Hz); positive means above the channel


@dataclass(frozen=True)
class HopAlignment:
    """An observed channel sequence, aligned against a hop pattern."""

    offset: int                # Pattern index of the first observation
    expected: Tuple[int, ...]  # The pattern's channel for each observation
    matches: Tuple[bool, ...]  # True where the observed channel matched the expected one
    num_matched: int           # Total matches


class ChannelPlan:
    """Channel numbers and their center frequencies (Hz)."""

    def __init__(self, channels: Mapping[int, float]):
        """Class ctor.

        Args:
            channels: Channel number -> center frequency (Hz).  Frequencies must be unique.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        # INPUT VALIDATION
        if not isinstance(channels, Mapping):
            raise TypeError(f"channels must be a Mapping, got {type(channels)}")
        if not channels:
            raise ValueError("channels must not be empty")
        for number, freq in channels.items():
            _validate_channel_number(number)
            if not isinstance(freq, (int, float)) or isinstance(freq, bool):
                raise TypeError(f"Channel {number} frequency must be a float, got {type(freq)}")
        if len(set(channels.values())) != len(channels):
            raise ValueError("Channel frequencies must be unique")

        # ATTRIBUTES (sorted by frequency, so resolve() can binary search them)
        pairs = sorted(channels.items(), key=lambda pair: pair[1])             # Sorted by freq
        self._numbers: Tuple[int, ...] = tuple(number for number, _ in pairs)  # Channel numbers
        self._freqs: np.ndarray = np.array([freq for _, freq in pairs])        # Center freqs
        self._by_number: dict[int, float] = dict(channels)                     # number -> freq

    @classmethod
    def create_from_grid(cls, first_freq: float, spacing: float, num_channels: int,
                         first_channel: int = 0) -> "ChannelPlan":
        """Create a plan of evenly spaced channels.

        Args:
            first_freq: Center frequency (Hz) of the first channel.
            spacing: Distance (Hz) between adjacent channel centers.
            num_channels: How many channels.
            first_channel: [OPTIONAL] Number of the first channel; the rest count up from it.

        Returns:
            A new ChannelPlan.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        if spacing <= 0:
            raise ValueError(f"spacing must be > 0, got {spacing}")
        if not isinstance(num_channels, int) or num_channels < 1:
            raise ValueError(f"num_channels must be an int >= 1, got {num_channels}")
        return cls({first_channel + index: first_freq + index * spacing
                    for index in range(num_channels)})

    def get_channels(self) -> Tuple[int, ...]:
        """Return every channel number, in frequency order."""
        return self._numbers

    def get_freq(self, channel: int) -> float:
        """Return a channel's center frequency (Hz).

        Raises:
            KeyError: Unknown channel.
        """
        return self._by_number[channel]

    def resolve(self, freq_hz: float, max_residual_hz: float | None = None) -> ChannelMatch:
        """Resolve a measured frequency to the nearest channel.

        Args:
            freq_hz: Measured frequency (Hz).
            max_residual_hz: [OPTIONAL] If the nearest channel is farther than this, report
                channel=None (no match) instead.  None always picks the nearest channel.

        Returns:
            The nearest channel, its frequency, and the residual.
        """
        # LOCAL VARIABLES
        right = int(np.searchsorted(self._freqs, freq_hz))  # First channel at/above freq_hz
        nearest = 0                                         # Index of the nearest channel
        residual = 0.0                                      # freq_hz minus nearest channel
        channel = None                                      # Matched channel number

        # RESOLVE IT (the nearest channel is right at the insertion point, or just left of it)
        if right == 0:
            nearest = 0
        elif right == self._freqs.size:
            nearest = right - 1
        elif freq_hz - self._freqs[right - 1] <= self._freqs[right] - freq_hz:
            nearest = right - 1
        else:
            nearest = right
        residual = float(freq_hz - self._freqs[nearest])
        if max_residual_hz is None or abs(residual) <= max_residual_hz:
            channel = self._numbers[nearest]

        # DONE
        return ChannelMatch(channel=channel, channel_freq=float(self._freqs[nearest]),
                            residual_hz=residual)


class HopPattern:
    """The cyclic sequence of channel numbers a transmitter hops through."""

    def __init__(self, channels: Sequence[int]):
        """Class ctor.

        Args:
            channels: Channel numbers in hop order.  The pattern repeats after the last one.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        if isinstance(channels, (str, bytes)) or not isinstance(channels, Sequence):
            raise TypeError(f"channels must be a Sequence of int, got {type(channels)}")
        if not channels:
            raise ValueError("channels must not be empty")
        for number in channels:
            _validate_channel_number(number)
        self._channels: Tuple[int, ...] = tuple(channels)  # Hop order

    def get_channels(self) -> Tuple[int, ...]:
        """Return the channel numbers, in hop order."""
        return self._channels

    def align(self, observed: Sequence[int | None]) -> HopAlignment:
        """Find where an observed channel sequence best lines up with the pattern.

        Tries every starting offset into the (cyclic) pattern and keeps the one with the most
        matches.  An observation of None (unresolved) never matches.

        Note: this aligns by burst ORDER, so a missed or extra burst shifts every later
        observation by one hop.  Watch for a run of matches that suddenly stops.

        Args:
            observed: Observed channel numbers, in burst order.

        Returns:
            The best alignment.
        """
        # LOCAL VARIABLES
        pattern = np.array(self._channels)                                # Pattern as an array
        obs = np.array([-1 if num is None else num for num in observed])  # None -> -1
        steps = np.arange(obs.size)                                       # 0..N-1
        best_offset = 0                                                   # Most matches
        best_matches = np.zeros(obs.size, dtype=bool)                     # Its matches
        matches = None                                                    # Matches at one offset

        # ALIGN IT
        for offset in range(pattern.size):
            matches = obs == pattern[(offset + steps) % pattern.size]
            if matches.sum() > best_matches.sum():
                best_offset, best_matches = offset, matches

        # DONE
        return HopAlignment(offset=best_offset,
                            expected=tuple(int(num) for num in
                                           pattern[(best_offset + steps) % pattern.size]),
                            matches=tuple(bool(hit) for hit in best_matches),
                            num_matched=int(best_matches.sum()))


@dataclass(frozen=True)
class FhssProfile:
    """A frequency-hopping spread spectrum (FHSS) system: its channel plan and hop pattern."""

    plan: ChannelPlan     # Channel numbers and center frequencies
    pattern: HopPattern   # Hop order, using the plan's channel numbers

    def __post_init__(self):
        """Validate that every hop lands on a channel the plan knows about."""
        if not isinstance(self.plan, ChannelPlan):
            raise TypeError(f"plan must be a ChannelPlan, got {type(self.plan)}")
        if not isinstance(self.pattern, HopPattern):
            raise TypeError(f"pattern must be a HopPattern, got {type(self.pattern)}")
        unknown = set(self.pattern.get_channels()) - set(self.plan.get_channels())
        if unknown:
            raise ValueError(f"The hop pattern uses channels not in the plan: {sorted(unknown)}")


def _validate_channel_number(number: int) -> None:
    """Validate a channel number on behalf of this module."""
    if not isinstance(number, int) or isinstance(number, bool):
        raise TypeError(f"Channel numbers must be int, got {type(number)}")
