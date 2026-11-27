"""Functionality to analyze data."""

# Standard Imports
from collections import Counter, defaultdict
from math import floor
from typing import List
# Third Party Imports
# Local Imports
from gallant_input.validation import (validate_bool, validate_bytes_or_str, validate_list,
                                      validate_pos_int)


def compare_streams(stream1: bytes | str, stream2: bytes | str, show_index: bool = True) -> int:
    """Compare two streams and print the differences.

    Args:
        stream1: The first stream to compare.
        stream2: The second stream to compare.
        show_index: [OPTIONAL] Include a line indicating the index (0-9).

    Returns:
        The number of differences between the two streams.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    prefix1 = 'STREAM1: '       # Identifying preface for stream 1
    prefix2 = 'STREAM2: '       # Identifying preface for stream 2
    index_prefix = 'INDEX:   '  # Identifying preface for the indices
    diff_prefix = 'NEQ:     '   # Identifying preface for the diff indicator
    max_len = 0                 # The length of the longest stream
    missing_char = '?'          # Missing character
    diff_char = '*'             # Difference character
    num_diffs = 0               # Number of differences

    # INPUT VALIDATION
    validate_bytes_or_str(stream1, 'stream1')
    validate_bytes_or_str(stream2, 'stream2')
    if not isinstance(stream1, type(stream2)):
        raise TypeError(f'The type of stream1 "{type(stream1)}" must be the same '
                        f'as stream2 "{type(stream2)}"')
    validate_bool(show_index, 'show_index')

    # PREPARE
    # Properly format the missing character
    missing_char = missing_char[0]
    if isinstance(stream1, bytes):
        missing_char = bytes(missing_char, 'ascii')
        index_prefix = index_prefix + '  '  # Python prints a b' prefix that misaligns output
        diff_prefix = diff_prefix + '  '  # Python prints a b' prefix that misaligns output
    # Determine the maximum length and pad the other stream (as applicable)
    max_len = len(stream1)
    if len(stream2) > max_len:
        max_len = len(stream2)
        stream1 = stream1 + missing_char * (max_len - len(stream1))  # Pad the stream
    elif max_len > len(stream2):
        stream2 = stream2 + missing_char * (max_len - len(stream2))  # Pad the stream

    # COMPARE IT
    print(f'{prefix1}{stream1}')
    print(f'{prefix2}{stream2}')
    if show_index:
        print(f'{index_prefix}{"".join([str(index % 10) for index in range(max_len)])}')
    print(diff_prefix, end='')
    for index in range(max_len):
        if stream1[index] != stream2[index]:
            print(diff_char, end='')
            num_diffs += 1
        else:
            print(' ', end='')
    print()  # Final line wrap

    # DONE
    return num_diffs


def find_common_prefix(stream_list: List[bytes | str]) -> bytes | str:
    """Find the longest common prefix (leading sub-string) shared by a list of objects.

    A list with one entry will result in returning the entry.  A list with no entries will
    raise an Exception.  The data type of all list entries must be the same.

    Args:
        stream_list: A list of objects to find the longest common prefix of.

    Returns:
        The longest prefix shared by all of the list entries.  If the entries don't all
        start the same way, the return value will be empty.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value: empty list, empty list entry.
    """
    # LOCAL VARIABLES
    prefix = None  # The longest common prefix

    # INPUT VALIDATION
    _validate_stream_list(stream_list)

    # FIND IT
    prefix = _find_common_prefix(stream_list)

    # DONE
    return prefix


def find_common_repeats(haystack: bytes | str, win_len: int = 24,
                        max_num: int = 1) -> List[tuple[bytes | str:int]]:
    """Find a certain number of the most common repeats of a certain length.

    1. Counts all the repeats of length "win_len"
    2. Finds the top "max_num" repeats
    3. Returns those values in a list of tuples

    Args:
        haystack: The object to search for repeating strings.
        win_len: The length of the substrings to count.  Value must exceed 0.
        max_num: The number of top repeaters to return (e.g., 3 == Return the top 3 repeats).
            Value must exceed 0.

    Returns:
        A list of the most common repeated substrings, of length "win_len" and their respective
        counts.  There is no guarantee that the length of the return value will be equal to max_num.

    Raises:
        TypeError: Bad data type.
        ValueError: Invalid integer.
    """
    # LOCAL VARIABLES
    counter_obj = None
    common_repeats = []  # The list of tuples

    # INPUT VALIDATION
    validate_bytes_or_str(haystack, 'haystack')
    validate_pos_int(win_len, 'win_len')
    validate_pos_int(max_num, 'max_num')

    # FIND IT
    counter_obj = _build_counter_obj(haystack, win_len)
    common_repeats = counter_obj.most_common(max_num)

    # DONE
    return common_repeats


def find_common_substrings(stream_list: List[bytes | str], win_len: int) -> set:
    """Find every substring of a given length that appears in all of the streams.

    Unlike find_common_prefix(), the substrings may appear anywhere in each stream, at
    different positions in different streams.  Use it to confirm a suspected sync word (e.g.,
    "11001101" in every burst) or to discover candidates of a given length.

    Args:
        stream_list: A list of objects to search.  Every entry must share one data type.
        win_len: The length of the substrings to find.  Value must exceed 0.

    Returns:
        A set of every substring of length win_len found in all of the streams (possibly empty).

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value: empty list, empty list entry, or bad win_len.
    """
    # LOCAL VARIABLES
    common = set()  # Substrings of length win_len found in every stream

    # INPUT VALIDATION
    _validate_stream_list(stream_list)
    validate_pos_int(win_len, 'win_len')

    # FIND THEM
    common = _find_common_substrings(stream_list, win_len)

    # DONE
    return common


def find_dense_repeat(haystack: bytes | str) -> tuple[bytes | str:int]:
    """Find the most dense repeating substring (count(substring) * len(subsring)) in the haystack.

    The substring will always be longer than a single character, and must occur at least twice
    (a substring seen once isn't a repeat).

    Args:
        haystack: The object to search for repeating strings.

    Returns:
        The first occurrence of the most dense substring in the haystack, as a tuple of
        (substring, count), or None if nothing repeats.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    repeats = []         # A list of the most common repeated substrings and their respective counts
    dense_repeat = None  # The first occurrence of the most dense repeat
    temp_density = 0     # Temp variable to hold a density (AKA len() * count())
    cur_winner = 0       # The len() * count of the current "most dense" winner

    # INPUT VALIDATION
    # Handled by find_common_repeats()

    # FIND IT
    # Find *all* the most common repeats for each length starting at half the haystack length
    for win_len in range(2, floor(len(haystack)/2)+1):
        repeats += find_common_repeats(haystack, win_len)
    # Keep the densest; a substring that occurs only once isn't a repeat
    for repeat in repeats:
        temp_density = len(repeat[0]) * repeat[1]
        if repeat[1] > 1 and temp_density > cur_winner:
            dense_repeat = repeat  # Current record holder for "most dense repeat"
            cur_winner = temp_density  # New record to beat

    # DONE
    return dense_repeat


def find_dense_repeats(haystack: bytes | str,
                       reverse: bool = False) -> List[tuple[bytes | str:int]]:
    """Recursively find the densed repeats in a haystack.

    The base case is the most repeated substring (within the most repeated substring, etc) found
    in the haystack.

    Args:
        haystack: The object to search for repeating strings.
        reverse: [OPTIONAL] If True, the first index of the return value will be the base case
            substring.

    Returns:
        A list of tuples that reference each other.  By default (reverse=False), each entry's
        index 0 will contain the index 0 of the next entry in the list.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    repeats = []  # List of recursive repeats

    # INPUT VALIDATION
    # haystack
    # Handled by find_common_repeats()
    # reverse
    validate_bool(reverse, 'reverse')

    # FIND THEM
    repeats = _find_dense_repeats(haystack)
    if reverse:
        repeats = repeats[::-1]

    # DONE
    return repeats


def find_longest_common_substrings(stream_list: List[bytes | str]) -> set:
    """Find the longest substrings that appear in all of the streams.

    Binary searches the substring length: if every stream shares a substring of length L, they
    also share one of every shorter length, so the longest shared length can be bracketed.

    Args:
        stream_list: A list of objects to search.  Every entry must share one data type.

    Returns:
        A set of every longest common substring (several may tie, e.g., rotations of a repeating
        preamble).  The set is empty if the streams share no characters at all.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value: empty list or empty list entry.
    """
    # LOCAL VARIABLES
    low = 1          # Shortest length still in question
    high = 0         # Longest length still in question
    mid = 0          # Length being tried
    common = set()   # Common substrings of length mid
    longest = set()  # Longest common substrings found so far

    # INPUT VALIDATION
    _validate_stream_list(stream_list)

    # FIND THEM
    high = min(len(entry) for entry in stream_list)  # No common substring outlasts the shortest
    while low <= high:
        mid = (low + high) // 2
        common = _find_common_substrings(stream_list, mid)
        if common:
            longest = common  # Every stream shares a substring this long; try longer
            low = mid + 1
        else:
            high = mid - 1  # Too long; try shorter

    # DONE
    return longest


def find_repeats(haystack: bytes | str, win_len: int = 24) -> dict:
    """Search haystack for repeats.

    Algorithm: Sliding Window + Hashing (Rabin–Karp).

    Args:
        haystack: The object to search for repeating strings.
        win_len: The length of each substring to compare.

    Returns:
        A dictionary of {sub-strings : indices}.
    """
    # LOCAL VARIABLES
    seen = defaultdict(list)  # Default dict
    window = b''              # The slice to investigate
    result = {}               # A dictionary of {sub-strings : indices}

    # FIND IT
    for i in range(len(haystack)-win_len+1):
        window = haystack[i:i+win_len]
        seen[window].append(i)
    result = {key: value for key, value in seen.items() if len(value) > 1}

    # DONE
    return result


def _build_counter_obj(haystack: bytes | str, win_len: int) -> Counter:
    """Build and return a Counter() object."""
    return Counter(haystack[i:i+win_len] for i in range(len(haystack)-win_len+1))


def _collect_substrings(stream: bytes | str, win_len: int) -> set:
    """Collect every distinct substring of length win_len in stream."""
    return {stream[index:index+win_len] for index in range(len(stream)-win_len+1)}


def _find_common_prefix(stream_list: List[bytes | str]) -> bytes | str:
    """Find the longest common prefix shared by a list of already validated objects."""
    # LOCAL VARIABLES
    prefix = stream_list[0]  # Working candidate for the prefix

    # FIND IT
    for next_stream in stream_list[1:]:
        prefix = _find_common_prefix_pair(next_stream, prefix)

    # DONE
    return prefix


def _find_common_prefix_pair(stream1: bytes | str, stream2: bytes | str) -> bytes | str:
    """Find the longest common prefix shared by two streams."""
    # LOCAL VARIABLES
    prefix = stream1[:0]   # Working candidate for the prefix
    long_stream = stream1  # Longest stream, default starting condition
    shrt_stream = stream2  # Shortest stream, default starting condition

    # PREPARE
    if len(stream2) > len(stream1):
        long_stream = stream2
        shrt_stream = stream1

    # FIND IT
    for index in range(len(shrt_stream), 0, -1):
        if long_stream.startswith(shrt_stream[:index]):
            prefix = shrt_stream[:index]  # Found it
            break  # Stop looking

    # DONE
    return prefix


def _find_common_substrings(stream_list: List[bytes | str], win_len: int) -> set:
    """Find every substring of length win_len present in all already validated streams."""
    # LOCAL VARIABLES
    by_length = sorted(stream_list, key=len)             # Shortest stream first: fewest
    common = _collect_substrings(by_length[0], win_len)  # Candidates from the shortest stream

    # FIND THEM (each later stream can only remove candidates)
    for stream in by_length[1:]:
        common = {candidate for candidate in common if candidate in stream}
        if not common:
            break  # Nothing left to find

    # DONE
    return common


def _find_dense_repeats(haystack: bytes | str) -> List[tuple[bytes | str:int]]:
    """Recursively find the densed repeats in a haystack.

    The base case is the most repeated substring (within the most repeated substring, etc) found
    in the haystack.

    Args:
        haystack: The object to search for repeating strings.

    Returns:
        A list of tuples that reference each other.  By default (reverse=False), each entry's
        index 0 will contain the index 0 of the next entry in the list.
    """
    # LOCAL VARIABLES
    repeats = []              # List of recursive repeats
    temp_dense_repeat = None  # Temp find_dense_repeat() return value

    # FIND THEM
    temp_dense_repeat = find_dense_repeat(haystack)
    if temp_dense_repeat:
        repeats.append(temp_dense_repeat)
        if temp_dense_repeat[0] != haystack:
            repeats += _find_dense_repeats(temp_dense_repeat[0])

    # DONE
    return repeats


def _validate_stream_list(stream_list: List[bytes | str]) -> None:
    """Validate a non-empty list of non-empty streams that all share one data type."""
    validate_list(stream_list, 'stream_list', can_be_empty=False)
    for stream_list_entry in stream_list:
        validate_bytes_or_str(stream_list_entry, 'stream_list entry')
        if not stream_list_entry:
            raise ValueError('The stream_list entries may not be empty')
        if not isinstance(stream_list_entry, type(stream_list[0])):
            raise TypeError('A data type mismatch was detected within the stream list: '
                            f'index 0 was of type "{type(stream_list[0])}" and then a '
                            f'type of "{type(stream_list_entry)}" was detected')
