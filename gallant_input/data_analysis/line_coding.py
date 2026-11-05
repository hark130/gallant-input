"""Functionality to identify the line coding of a symbol stream (e.g., Manchester, NRZI).

A "symbol stream" is a string (or bytes) of "0"s and "1"s, one character per demodulated symbol,
as read from a tool like Inspectrum.  For Manchester coding, each symbol is a chip (AKA half-bit)
and two chips make one data bit.

    Typical usage example:

    from gallant_input.data_analysis.line_coding import evaluate_manchester_coding
    from gallant_input.data_analysis.manchesterverdict import ManchesterVerdict

    evaluation = evaluate_manchester_coding("1100110101010011...")
    if evaluation.verdict == ManchesterVerdict.MANCHESTER:
        print(evaluation.decoded_bits)
"""

# Standard Imports
from collections import Counter
from dataclasses import replace
from functools import reduce
from math import comb, floor, gcd, log2
from typing import Final
import re
# Third Party Imports
# Local Imports
from gallant_input.data_analysis.encodingscheme import EncodingScheme
from gallant_input.data_analysis.manchesterevaluation import ManchesterEvaluation
from gallant_input.data_analysis.manchesterverdict import ManchesterVerdict
from gallant_input.validation import (validate_bool, validate_bytes_or_str, validate_float,
                                      validate_int, validate_pos_int, validate_string)


# Manchester conventions: the chip pair that decodes to a 1
IEEE_ONE_PAIR: Final[str] = "01"    # IEEE 802.3: 1 is low-to-high, so the 2nd chip equals the bit
THOMAS_ONE_PAIR: Final[str] = "10"  # G.E. Thomas: 1 is high-to-low, so the 1st chip equals the bit
UNKNOWN_BIT: Final[str] = "?"       # Decoded value of an illegal ("00"/"11") pair

# Default thresholds for evaluate_manchester_coding()
MAX_ERROR_RATE: Final[float] = 0.02         # Tolerated fraction of clean offset illegal pairs
MIN_PAIRS: Final[int] = 64                  # Fewest whole pairs needed to reach any verdict
MIN_TRANSITIONS: Final[int] = 16            # Fewest data transitions needed
MIN_EVIDENCE_BITS: Final[float] = 30.0      # Fewest bits of evidence against random chips
MAX_DISPARITY: Final[int] = 2               # Largest running disparity of clean Manchester chips
MAX_REPEAT_PERIOD: Final[int] = 64          # Longest repetition period to search for diff. evidence
MIN_REPEAT_CORRELATION: Final[float] = 0.5  # Smallest |autocorrelation| that counts as a repetition
SLIP_WINDOW_PAIRS: Final[int] = 32          # Pairs per window when hunting for symbol slips


def calculate_evidence_bits(num_pairs: int, num_violations: int, num_offsets: int = 2) -> float:
    """Calculate how surprising a clean pair alignment would be if the chips were random.

    For random chips, each aligned pair is legal ("01"/"10") with a probability of 0.5.  This
    function returns -log2(P), where P is the probability of seeing num_violations or fewer
    illegal pairs out of num_pairs by chance (a binomial tail), less the bits spent picking the
    best of num_offsets alignments.  Higher is stronger evidence; 20-30+ bits is overwhelming.

    NOTE: This measures evidence against *random chips*, not the probability of Manchester.
    A long "0101..." run scores high here too, so pair it with a check for data transitions.

    Args:
        num_pairs: The number of whole pairs evaluated.  Must be zero or greater.
        num_violations: The number of illegal pairs found.  Must be 0 to num_pairs.
        num_offsets: [OPTIONAL] The number of alignments that were tried.  Must exceed 0.

    Returns:
        The bits of evidence against random chips, never less than 0.0.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    ways = 0             # Number of ways to see num_violations or fewer illegal pairs
    evidence_bits = 0.0  # The bits of evidence

    # INPUT VALIDATION
    _validate_count(num_pairs, "num_pairs")
    _validate_count(num_violations, "num_violations")
    if num_violations > num_pairs:
        raise ValueError(f"num_violations ({num_violations}) may not exceed "
                         f"num_pairs ({num_pairs})")
    validate_pos_int(num_offsets, "num_offsets")

    # CALCULATE IT
    ways = sum(comb(num_pairs, k) for k in range(num_violations + 1))
    evidence_bits = max(0.0, num_pairs - log2(ways) - log2(num_offsets))

    # DONE
    return evidence_bits


def calculate_max_disparity(symbols: bytes | str) -> int:
    """Calculate the largest absolute running disparity (+1 per "1", -1 per "0").

    This measures DC (direct current) balance: the average value of the stream when treated as a
    +1/-1 waveform.  Every legal Manchester pair adds exactly zero, so clean Manchester chips stay
    within +/-2 regardless of offset.  NRZ (Non-Return-to-Zero) data usually wanders far beyond.

    Args:
        symbols: The symbol stream: "0"s and "1"s.

    Returns:
        The largest absolute value the running disparity reached.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    chips = ""         # Validated symbol stream
    disparity = 0      # Running disparity
    max_disparity = 0  # Largest absolute disparity seen

    # INPUT VALIDATION
    chips = _convert_symbol_stream(symbols, "symbols")

    # CALCULATE IT
    for chip in chips:
        disparity += 1 if chip == "1" else -1
        max_disparity = max(max_disparity, abs(disparity))

    # DONE
    return max_disparity


def calculate_run_length_gcd(symbols: bytes | str) -> int:
    """Calculate the GCD (Greatest Common Divisor) of the interior run lengths.

    The first and last runs are ignored because the burst edges cut them short.  A GCD of k > 1
    suggests the symbol rate was set k times too high, so every true symbol was read k times.

    Args:
        symbols: The symbol stream: "0"s and "1"s.

    Returns:
        The GCD of the interior run lengths, or 0 if there are no interior runs.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    run_lengths = Counter()  # Histogram of interior run lengths
    run_gcd = 0              # GCD of the run lengths

    # INPUT VALIDATION
    # Handled by measure_run_lengths()

    # CALCULATE IT
    run_lengths = measure_run_lengths(symbols)
    if run_lengths:
        run_gcd = reduce(gcd, run_lengths.keys())

    # DONE
    return run_gcd


def count_illegal_pairs(symbols: bytes | str, offset: int) -> int:
    """Count the illegal Manchester pairs ("00"/"11") at a given chip offset.

    Args:
        symbols: The symbol stream: "0"s and "1"s.
        offset: The chip to start pairing at: 0 or 1.

    Returns:
        The number of illegal pairs.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    return len(locate_illegal_pairs(symbols, offset))


def decode_manchester(symbols: bytes | str, offset: int, one_pair: str = IEEE_ONE_PAIR) -> str:
    """Decode a Manchester-coded symbol stream into bits.

    Illegal pairs ("00"/"11") decode as UNKNOWN_BIT so their positions are preserved.

    Args:
        symbols: The symbol stream: "0"s and "1"s.
        offset: The chip to start pairing at: 0 or 1.
        one_pair: [OPTIONAL] The chip pair that decodes to a 1: IEEE_ONE_PAIR ("01") or
            THOMAS_ONE_PAIR ("10").

    Returns:
        The decoded bits as a string.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    chips = ""         # Validated symbol stream
    zero_pair = ""     # The chip pair that decodes to a 0
    decoded_bits = []  # The decoded bits

    # INPUT VALIDATION
    chips = _convert_symbol_stream(symbols, "symbols")
    _validate_offset(offset, "offset")
    validate_string(one_pair, "one_pair")
    if one_pair not in (IEEE_ONE_PAIR, THOMAS_ONE_PAIR):
        raise ValueError(f'one_pair must be "{IEEE_ONE_PAIR}" or "{THOMAS_ONE_PAIR}", '
                         f'not "{one_pair}"')

    # DECODE IT
    zero_pair = one_pair[::-1]
    for pair in _split_pairs(chips, offset):
        if pair == one_pair:
            decoded_bits.append("1")
        elif pair == zero_pair:
            decoded_bits.append("0")
        else:
            decoded_bits.append(UNKNOWN_BIT)

    # DONE
    return "".join(decoded_bits)


def decode_transitions(bits: bytes | str, change_is_one: bool = True) -> str:
    """Differentially decode bits: each output bit says whether the input level changed.

    This is the NRZI (Non-Return-to-Zero Inverted) decode.  Apply it to a symbol stream for NRZI,
    or to Manchester-decoded bits for differential Manchester.  The output is one bit shorter than
    the input and does not depend on polarity (inverting the input gives the same output).
    UNKNOWN_BIT inputs produce UNKNOWN_BIT outputs.

    Args:
        bits: The bits to decode: "0"s, "1"s, and UNKNOWN_BITs.
        change_is_one: [OPTIONAL] If True, a level change decodes to 1.  If False, to 0.

    Returns:
        The differentially decoded bits as a string.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    in_bits = ""                             # Validated bits
    changed = "1" if change_is_one else "0"  # Output for a change
    held = "0" if change_is_one else "1"     # Output for no change
    decoded_bits = []                        # The decoded bits

    # INPUT VALIDATION
    in_bits = _convert_symbol_stream(bits, "bits", allow_unknown=True)
    validate_bool(change_is_one, "change_is_one")

    # DECODE IT
    for prev_bit, next_bit in zip(in_bits, in_bits[1:]):
        if UNKNOWN_BIT in (prev_bit, next_bit):
            decoded_bits.append(UNKNOWN_BIT)
        elif prev_bit != next_bit:
            decoded_bits.append(changed)
        else:
            decoded_bits.append(held)

    # DONE
    return "".join(decoded_bits)


def detect_differential_encoding(bits: bytes | str, max_period: int = MAX_REPEAT_PERIOD,
                                 min_correlation: float = MIN_REPEAT_CORRELATION) -> bool:
    """Detect evidence of differential encoding from repeated content.

    When a transmitter repeats a word, a differential encoder leaves the level flipped after each
    repetition if the word has an odd number of 1s.  The (non-differentially) decoded stream then
    alternates between the word and its complement (W, ~W, W, ...), which shows up as a strong
    negative autocorrelation at the repetition period.  If transition-decoding turns that into a
    strong positive autocorrelation, differential encoding is likely.

    NOTE: A False return value means "no evidence," not "not differential."  Streams without
    repetition, or whose repeated words have an even number of 1s, carry no evidence either way.

    Args:
        bits: The bits to check (a symbol stream for NRZ vs NRZI, or Manchester-decoded bits for
            Manchester vs differential Manchester).
        max_period: [OPTIONAL] The longest repetition period to search.  Must exceed 1.
        min_correlation: [OPTIONAL] The smallest |autocorrelation| that counts as a repetition.
            Must be greater than 0.0 and no more than 1.0.

    Returns:
        True if the repetitions alternate polarity and transition-decoding fixes that.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    in_bits = ""       # Validated bits
    period = 0         # Repetition period
    correlation = 0.0  # Correlation at period
    found = False      # Evidence found?

    # INPUT VALIDATION
    in_bits = _convert_symbol_stream(bits, "bits", allow_unknown=True)
    # max_period and min_correlation are handled by measure_repetition_polarity()

    # DETECT IT
    period, correlation = measure_repetition_polarity(in_bits, max_period, min_correlation)
    if period and correlation <= -min_correlation:
        found = _correlate_at_lag(_convert_bits_to_values(decode_transitions(in_bits)),
                                  period) >= min_correlation

    # DONE
    return found


def evaluate_manchester_coding(symbols: bytes | str, max_error_rate: float = MAX_ERROR_RATE,
                               log_findings: bool = True) -> ManchesterEvaluation:
    """Evaluate a symbol stream as Manchester coding, then log the findings.

    1. Measures pair legality at both offsets, evidence bits, DC balance, run lengths, and slips
    2. Decides a verdict (and a best-guess encoding scheme) from those measurements
    3. Decodes the stream per the best guess, checking for differential encoding along the way
    4. Logs the findings (optional)

    Args:
        symbols: The symbol stream: "0"s and "1"s.
        max_error_rate: [OPTIONAL] Tolerated fraction of illegal pairs at the clean offset, to
            account for bit errors.  Must be at least 0.0 and less than 0.5.
        log_findings: [OPTIONAL] If True, prints the findings.

    Returns:
        A ManchesterEvaluation describing the measurements, verdict, and reasoning.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    chips = ""         # Validated symbol stream
    evaluation = None  # The findings

    # INPUT VALIDATION
    chips = _convert_symbol_stream(symbols, "symbols")
    _validate_error_rate(max_error_rate, "max_error_rate")
    validate_bool(log_findings, "log_findings")

    # EVALUATE IT
    evaluation = _measure_stream(chips, max_error_rate)
    evaluation = _judge_evaluation(evaluation, chips, max_error_rate)
    evaluation = _decode_best_guess(evaluation, chips)
    if log_findings:
        _log_evaluation(evaluation)

    # DONE
    return evaluation


def find_alignment_slips(symbols: bytes | str, window_pairs: int = SLIP_WINDOW_PAIRS,
                         max_error_rate: float = MAX_ERROR_RATE) -> list[int]:
    """Find where the clean Manchester offset flips, which usually means a symbol slip.

    The stream is split into windows of window_pairs pairs.  A window is "clean" at an offset if
    that offset is within max_error_rate and the other offset is not.  Ambiguous windows (e.g.,
    a "0101..." run, which is clean at both offsets) are skipped.  A change in the clean offset
    between windows is reported at the start of the window where it was first seen, so the true
    slip is somewhere in the preceding window or two.

    Args:
        symbols: The symbol stream: "0"s and "1"s.
        window_pairs: [OPTIONAL] The number of pairs per window.  Must exceed 0.
        max_error_rate: [OPTIONAL] Tolerated fraction of illegal pairs at the clean offset.
            Must be at least 0.0 and less than 0.5.

    Returns:
        A list of chip indices where the clean offset flipped.  Empty if no flips were found.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    chips = ""           # Validated symbol stream
    window_len = 0       # Window length, in chips
    limit = 0            # Most illegal pairs a clean window has
    counts = (0, 0)      # Illegal pairs at offsets 0 and 1
    clean_offset = None  # Clean offset of the current window
    prev_offset = None   # Clean offset of the last clean window
    slip_indices = []    # Chip indices of the flips

    # INPUT VALIDATION
    chips = _convert_symbol_stream(symbols, "symbols")
    validate_pos_int(window_pairs, "window_pairs")
    _validate_error_rate(max_error_rate, "max_error_rate")

    # FIND THEM
    window_len = 2 * window_pairs  # Even, so window offsets match the stream offsets
    limit = floor(max_error_rate * window_pairs)
    for start in range(0, len(chips) - window_len + 1, window_len):
        counts = _count_illegal_pairs(chips[start:start + window_len])
        clean_offset = None
        if counts[0] <= limit < counts[1]:
            clean_offset = 0
        elif counts[1] <= limit < counts[0]:
            clean_offset = 1
        if clean_offset is not None:
            if prev_offset is not None and clean_offset != prev_offset:
                slip_indices.append(start)
            prev_offset = clean_offset

    # DONE
    return slip_indices


def locate_illegal_pairs(symbols: bytes | str, offset: int) -> list[int]:
    """Locate the illegal Manchester pairs ("00"/"11") at a given chip offset.

    Args:
        symbols: The symbol stream: "0"s and "1"s.
        offset: The chip to start pairing at: 0 or 1.

    Returns:
        A list of the chip indices where each illegal pair starts.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    chips = ""            # Validated symbol stream
    illegal_indices = []  # Chip indices of illegal pairs

    # INPUT VALIDATION
    chips = _convert_symbol_stream(symbols, "symbols")
    _validate_offset(offset, "offset")

    # LOCATE THEM
    for pair_index, pair in enumerate(_split_pairs(chips, offset)):
        if pair[0] == pair[1]:
            illegal_indices.append(offset + 2 * pair_index)

    # DONE
    return illegal_indices


def measure_max_run(symbols: bytes | str) -> int:
    """Measure the longest run of identical symbols, including the edge runs.

    Manchester chips never exceed 2.  4B5B allows up to 4, and 8b/10b allows up to 5.

    Args:
        symbols: The symbol stream: "0"s and "1"s.

    Returns:
        The length of the longest run.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    return max(_find_run_lengths(_convert_symbol_stream(symbols, "symbols")))


def measure_repetition_polarity(bits: bytes | str, max_period: int = MAX_REPEAT_PERIOD,
                                min_correlation: float = MIN_REPEAT_CORRELATION
                                ) -> tuple[int, float]:
    """Measure the repetition period of a stream and whether repeats keep or flip polarity.

    Bits are mapped to +1/-1 (UNKNOWN_BITs to 0) and autocorrelated at each lag.  The shortest lag
    whose |autocorrelation| meets min_correlation wins.  If none do, the strongest lag wins.
    Positive means the content repeats (W, W, ...).  Negative means it alternates with its
    complement (W, ~W, ...), which is a hint to try decode_transitions().

    Args:
        bits: The bits to measure: "0"s, "1"s, and UNKNOWN_BITs.
        max_period: [OPTIONAL] The longest lag to try.  Must exceed 1.
        min_correlation: [OPTIONAL] The |autocorrelation| that ends the search early.  Must be
            greater than 0.0 and no more than 1.0.

    Returns:
        A tuple of (period, normalized correlation from -1.0 to 1.0).  The period is 0 if the
        stream is too short to try any lag.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    in_bits = ""       # Validated bits
    values = []        # Bits mapped to +/-1
    correlation = 0.0  # Correlation at a lag
    best = (0, 0.0)    # (period, correlation)

    # INPUT VALIDATION
    in_bits = _convert_symbol_stream(bits, "bits", allow_unknown=True)
    validate_int(max_period, "max_period")
    if max_period < 2:
        raise ValueError(f"max_period must exceed 1, not {max_period}")
    validate_float(min_correlation, "min_correlation")
    if not 0.0 < min_correlation <= 1.0:
        raise ValueError(f"min_correlation must be in (0.0, 1.0], not {min_correlation}")

    # MEASURE IT
    values = _convert_bits_to_values(in_bits)
    for lag in range(2, min(max_period, len(values) // 2) + 1):
        correlation = _correlate_at_lag(values, lag)
        if abs(correlation) > abs(best[1]):
            best = (lag, correlation)
        if abs(correlation) >= min_correlation:
            best = (lag, correlation)
            break  # Shortest qualifying period found

    # DONE
    return best


def measure_run_lengths(symbols: bytes | str, include_edges: bool = False) -> Counter:
    """Measure the run lengths of a symbol stream as a histogram.

    Manchester chips only produce runs of 1 and 2, and should produce both.  Only 1s means a
    "0101..." run (constant Manchester data, or an NRZ preamble), which is ambiguous.

    Args:
        symbols: The symbol stream: "0"s and "1"s.
        include_edges: [OPTIONAL] If True, include the first and last runs, which the burst
            edges may have cut short.

    Returns:
        A Counter of {run length: number of runs}.  May be empty if include_edges is False.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    chips = ""        # Validated symbol stream
    run_lengths = []  # Every run length, in order

    # INPUT VALIDATION
    chips = _convert_symbol_stream(symbols, "symbols")
    validate_bool(include_edges, "include_edges")

    # MEASURE THEM
    run_lengths = _find_run_lengths(chips)
    if not include_edges:
        run_lengths = run_lengths[1:-1]

    # DONE
    return Counter(run_lengths)


def _convert_bits_to_values(bits: str) -> list[int]:
    """Convert bits to +1/-1 values, mapping UNKNOWN_BITs to 0."""
    return [1 if bit == "1" else -1 if bit == "0" else 0 for bit in bits]


def _convert_symbol_stream(symbols: bytes | str, param_name: str,
                           allow_unknown: bool = False) -> str:
    """Validate a symbol stream and convert it to a string of "0"s and "1"s (and UNKNOWN_BITs).

    Raises:
        TypeError: Bad data type.
        ValueError: Empty stream or illegal characters.
    """
    # LOCAL VARIABLES
    chips = ""                                                        # Converted symbol stream
    legal = {"0", "1", UNKNOWN_BIT} if allow_unknown else {"0", "1"}  # Legal characters
    illegal = set()                                                   # Illegal characters found

    # INPUT VALIDATION
    validate_bytes_or_str(symbols, param_name)

    # CONVERT IT
    if isinstance(symbols, bytes):
        try:
            chips = symbols.decode("ascii")
        except UnicodeDecodeError as err:
            raise ValueError(f"{param_name} must contain ASCII characters only") from err
    else:
        chips = symbols
    if not chips:
        raise ValueError(f"{param_name} may not be empty")
    illegal = set(chips) - legal
    if illegal:
        raise ValueError(f"{param_name} contains illegal characters: {sorted(illegal)}")

    # DONE
    return chips


def _correlate_at_lag(values: list[int], lag: int) -> float:
    """Normalized autocorrelation (-1.0 to 1.0) of +1/-1 values at one lag."""
    # LOCAL VARIABLES
    num_products = len(values) - lag  # Number of overlapping values
    correlation = 0.0                 # Normalized autocorrelation

    # CORRELATE IT
    if num_products > 0:
        correlation = sum(x * y for x, y in zip(values, values[lag:])) / num_products

    # DONE
    return correlation


def _count_illegal_pairs(chips: str) -> tuple[int, int]:
    """Count the illegal pairs at offsets 0 and 1 of an already validated stream."""
    return tuple(sum(pair[0] == pair[1] for pair in _split_pairs(chips, offset))
                 for offset in (0, 1))


def _decode_best_guess(evaluation: ManchesterEvaluation, chips: str) -> ManchesterEvaluation:
    """Decode the stream per the verdict and check for differential encoding."""
    # LOCAL VARIABLES
    scheme = evaluation.scheme  # Best-guess encoding scheme
    decoded_bits = ""           # Best-guess decode
    note = ""                   # Explanation of the decode

    # DECODE IT
    if evaluation.verdict == ManchesterVerdict.MANCHESTER:
        decoded_bits = decode_manchester(chips, evaluation.best_offset)
        if detect_differential_encoding(decoded_bits):
            scheme = EncodingScheme.DIFF_MANCHESTER
            decoded_bits = decode_transitions(decoded_bits)
            note = ("Repeated content alternates with its complement after Manchester decoding "
                    "and repeats cleanly after transition decoding: likely differential "
                    "Manchester (decoded bits are transition-decoded; change = 1)")
        else:
            note = (f'Decoded with the IEEE 802.3 convention ("{IEEE_ONE_PAIR}" = 1); invert '
                    "for G.E. Thomas.  No differential evidence (not ruled out either)")
    elif evaluation.scheme == EncodingScheme.NRZ:
        if detect_differential_encoding(chips):
            scheme = EncodingScheme.NRZI
            decoded_bits = decode_transitions(chips)
            note = ("Repeated content alternates with its complement and repeats cleanly after "
                    "transition decoding: likely NRZI (decoded bits use change = 1)")
        else:
            decoded_bits = chips
            note = "Assuming plain NRZ: no differential evidence (not ruled out either)"

    # DONE
    return replace(evaluation, scheme=scheme, decoded_bits=decoded_bits,
                   notes=evaluation.notes + [note] if note else evaluation.notes)


def _find_run_lengths(chips: str) -> list[int]:
    """Find the length of every run of identical symbols, in order."""
    return [len(match.group()) for match in re.finditer(r"0+|1+", chips)]


def _judge_evaluation(evaluation: ManchesterEvaluation, chips: str,
                      max_error_rate: float) -> ManchesterEvaluation:
    """Decide a verdict, and a best-guess encoding scheme, from the measurements."""
    # LOCAL VARIABLES
    best_count = 0                            # Illegal pairs at the best offset
    other_count = 0                           # Illegal pairs at the other offset
    best_rate = 0.0                           # Error rate at the best offset
    other_rate = 0.0                          # Error rate at the other offset
    num_changes = 0                           # Symbol transitions in the stream
    verdict = ManchesterVerdict.INCONCLUSIVE  # Is it Manchester?
    scheme = EncodingScheme.UNKNOWN           # Best-guess scheme
    note = ""                                 # Reason for the verdict

    # PREPARE
    best_count = evaluation.illegal_pairs[evaluation.best_offset]
    other_count = evaluation.illegal_pairs[1 - evaluation.best_offset]
    best_rate = best_count / max(evaluation.num_pairs, 1)  # Avoid dividing by zero
    other_rate = other_count / max(evaluation.num_pairs, 1)  # Avoid dividing by zero
    num_changes = sum(prev != this for prev, this in zip(chips, chips[1:]))

    # JUDGE IT
    if evaluation.num_pairs < MIN_PAIRS:
        note = f"Too short: {evaluation.num_pairs} pairs, need at least {MIN_PAIRS}"
    elif num_changes < MIN_TRANSITIONS:
        note = f"Too few symbol transitions: {num_changes}, need at least {MIN_TRANSITIONS}"
    elif best_rate <= max_error_rate and other_rate >= 1 - max_error_rate:
        note = ('Ambiguous "1100..." pattern: Manchester-coded alternating data, or 2x '
                "oversampled alternating NRZ")
    elif other_rate >= 1 - max_error_rate:
        verdict = ManchesterVerdict.NOT_MANCHESTER
        scheme = EncodingScheme.OVERSAMPLED_NRZ
        note = (f"Offset {1 - evaluation.best_offset} pairs are {other_rate:.0%} \"00\"/\"11\": "
                "likely NRZ read twice per symbol; re-read at half the symbol rate "
                f"(run length GCD = {evaluation.run_length_gcd})")
    elif best_rate > max_error_rate and evaluation.slip_indices:
        note = ("No single clean offset, but windows are clean at alternating offsets: likely "
                "Manchester with symbol slip(s); split the stream at the slip(s) and re-evaluate "
                "each piece")
    elif best_rate > max_error_rate:
        verdict = ManchesterVerdict.NOT_MANCHESTER
        scheme = EncodingScheme.NRZ
        note = f"No clean offset: the best has {best_rate:.1%} illegal pairs"
    elif other_count < MIN_TRANSITIONS:
        note = (f"Both offsets are clean (only {other_count} data transitions): likely a "
                '"0101..." run, which is constant data or an NRZ preamble')
    elif evaluation.evidence_bits < MIN_EVIDENCE_BITS:
        note = (f"Weak evidence: {evaluation.evidence_bits:.1f} bits, need at least "
                f"{MIN_EVIDENCE_BITS:.1f}")
    elif evaluation.max_disparity > MAX_DISPARITY + 2 * best_count:
        note = ("Pairs look clean but the running disparity reached "
                f"{evaluation.max_disparity}; check for a corrupted capture")
    else:
        verdict = ManchesterVerdict.MANCHESTER
        scheme = EncodingScheme.MANCHESTER
        note = (f"Offset {evaluation.best_offset} is clean ({best_count}/{evaluation.num_pairs} "
                f"illegal pairs) while offset {1 - evaluation.best_offset} has {other_count}; "
                f"{evaluation.evidence_bits:.0f} bits of evidence")

    # DONE
    return replace(evaluation, verdict=verdict, scheme=scheme, notes=evaluation.notes + [note])


def _log_evaluation(evaluation: ManchesterEvaluation) -> None:
    """Log the findings of a Manchester evaluation."""
    print(f"Manchester verdict: {evaluation.verdict.name} "
          f"(best guess: {evaluation.scheme.name})")
    print(f"    Illegal pairs at offsets 0/1: {evaluation.illegal_pairs[0]}/"
          f"{evaluation.illegal_pairs[1]} (best offset {evaluation.best_offset}, "
          f"{evaluation.num_pairs} pairs)")
    print(f"    Evidence: {evaluation.evidence_bits:.1f} bits; max disparity: "
          f"{evaluation.max_disparity}; run length GCD: {evaluation.run_length_gcd}")
    for note in evaluation.notes:
        print(f"    {note}")
    if evaluation.decoded_bits:
        print(f"    Decoded ({len(evaluation.decoded_bits)} bits): "
              f"{evaluation.decoded_bits}")


def _measure_stream(chips: str, max_error_rate: float) -> ManchesterEvaluation:
    """Take every measurement of an already validated stream, leaving the verdict undecided."""
    # LOCAL VARIABLES
    illegal_pairs = (0, 0)  # Illegal pairs at offsets 0 and 1
    best_offset = 0         # Offset with the fewest illegal pairs
    num_pairs = 0           # Whole pairs at the best offset
    slip_indices = []       # Chip indices of possible symbol slips
    notes = []              # Reasoning

    # MEASURE IT
    illegal_pairs = _count_illegal_pairs(chips)
    if illegal_pairs[1] < illegal_pairs[0]:
        best_offset = 1
    num_pairs = (len(chips) - best_offset) // 2
    slip_indices = find_alignment_slips(chips, max_error_rate=max_error_rate)
    if slip_indices:
        notes.append(f"The clean offset flips near chip(s) {slip_indices}: possible symbol "
                     "slip(s); check the symbol rate and grid alignment there")

    # DONE
    return ManchesterEvaluation(verdict=ManchesterVerdict.INCONCLUSIVE,
                                scheme=EncodingScheme.UNKNOWN,
                                best_offset=best_offset,
                                illegal_pairs=illegal_pairs,
                                num_pairs=num_pairs,
                                evidence_bits=calculate_evidence_bits(
                                    num_pairs, illegal_pairs[best_offset]),
                                max_disparity=calculate_max_disparity(chips),
                                run_length_gcd=calculate_run_length_gcd(chips),
                                slip_indices=slip_indices,
                                decoded_bits="",
                                notes=notes)


def _split_pairs(chips: str, offset: int) -> list[str]:
    """Split a stream into whole chip pairs, starting at offset."""
    return [chips[index:index + 2] for index in range(offset, len(chips) - 1, 2)]


def _validate_count(validate_this: int, param_name: str) -> None:
    """Validate validate_this as an integer of zero or greater."""
    validate_int(validate_this, param_name)
    if validate_this < 0:
        raise ValueError(f"{param_name} may not be negative, not {validate_this}")


def _validate_error_rate(validate_this: float, param_name: str) -> None:
    """Validate validate_this as a float error rate in [0.0, 0.5)."""
    validate_float(validate_this, param_name)
    if not 0.0 <= validate_this < 0.5:
        raise ValueError(f"{param_name} must be in [0.0, 0.5), not {validate_this}")


def _validate_offset(validate_this: int, param_name: str) -> None:
    """Validate validate_this as a chip offset: 0 or 1."""
    validate_int(validate_this, param_name)
    if validate_this not in (0, 1):
        raise ValueError(f"{param_name} must be 0 or 1, not {validate_this}")
