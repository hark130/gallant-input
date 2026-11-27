"""Defines the ManchesterEvaluation dataclass."""

# Standard Imports
from dataclasses import dataclass
# Third Party Imports
# Local Imports
from gallant_input.data_analysis.encodingscheme import EncodingScheme
from gallant_input.data_analysis.manchesterverdict import ManchesterVerdict


# pylint: disable=too-many-instance-attributes
@dataclass(frozen=True)
class ManchesterEvaluation:
    """Describes the findings of evaluating a symbol stream as Manchester coding."""

    verdict: ManchesterVerdict      # Is it Manchester coded?
    scheme: EncodingScheme          # Best guess at the line coding
    best_offset: int                # Chip offset (0 or 1) with the fewest illegal pairs
    illegal_pairs: tuple[int, int]  # Illegal ("00"/"11") pair counts at offsets 0 and 1
    num_pairs: int                  # Number of whole pairs at the best offset
    evidence_bits: float            # -log2(chance random chips are this clean)
    max_disparity: int              # Largest absolute running disparity (DC balance)
    run_length_gcd: int             # GCD of the interior run lengths
    slip_indices: list[int]         # Chip indices where the clean offset appears to flip
    decoded_bits: str               # Best-guess decode ("" if not Manchester or NRZI)
    notes: list[str]                # Human-readable reasoning behind the verdict
