"""Bit-level data analysis: repeats, stream comparison, and line coding."""

# Local Imports
from gallant_input.data_analysis.data_analysis import (compare_streams, find_common_prefix,
                                                       find_common_repeats,
                                                       find_common_substrings,
                                                       find_dense_repeat, find_dense_repeats,
                                                       find_longest_common_substrings,
                                                       find_repeats)

__all__ = ["compare_streams", "find_common_prefix", "find_common_repeats",
           "find_common_substrings", "find_dense_repeat", "find_dense_repeats",
           "find_longest_common_substrings", "find_repeats"]
