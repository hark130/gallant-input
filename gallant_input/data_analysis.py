"""Functionality to analyze data."""

# Standard Imports
from collections import Counter, defaultdict
from math import floor
from typing import List
# Third Party Imports
# Local Imports
from gallant_input.validation import (validate_bytes_or_str, validate_list, validate_pos_int,
                                      validate_type)


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
    validate_type(show_index, 'show_index', bool)

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
        print(f'{index_prefix}{"".join([str(index%10) for index in range(max_len)])}')
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


def find_dense_repeat(haystack: bytes | str) -> tuple[bytes | str:int]:
    """Find the most dense repeating substring (count(substring) * len(subsring)) in the haystack.

    The substring will always be longer than a single character.

    Args:
        haystack: The object to search for repeating strings.

    Returns:
        The first occurrence of the most dense substring in the haystack.

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
    # Set a benchmark to compare the rest of the results against
    if repeats:
        dense_repeat = repeats[0]  # This is the starting benchmark
        cur_winner = len(dense_repeat[0]) * dense_repeat[1]
    # Check for values that exceed the current benchmark
    for repeat in repeats:
        temp_density = len(repeat[0]) * repeat[1]
        if temp_density > cur_winner:
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
    validate_type(reverse, 'reverse', bool)

    # FIND THEM
    repeats = _find_dense_repeats(haystack)
    if reverse:
        repeats = repeats[::-1]

    # DONE
    return repeats


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


def find_stream_lcd(stream_list: List[bytes | str]) -> bytes | str:
    """Find the leading common sub-string among a list of objects.

    A list with one entry will result in returning the entry.  A list with no entries will
    raise an Exception.  The data type of all list entries must be the same.

    Args:
        stream_list: A list of objects to find the least common leading sub-string for.

    Returns:
        The least common leading sub-string between all of the list entries.  If there is no
        overlap between the entries, the return value will be empty.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value: empty list, empty list entry.
    """
    # LOCAL VARIABLES
    stream_lcd = None  # The stream least common preamble

    # INPUT VALIDATION
    validate_list(stream_list, 'stream_list', can_be_empty=False)
    for stream_list_entry in stream_list:
        validate_bytes_or_str(stream_list_entry, 'stream_list entry')
        if not stream_list_entry:
            raise ValueError('The stream_list entries may not be empty')
        if not isinstance(stream_list_entry, type(stream_list[0])):
            raise TypeError('A data type mismatch was detected within the stream list: '
                            f'index 0 was of type "{type(stream_list[0])}" and then a '
                            f'type of "{type(stream_list_entry)}" was detected')

    # FIND IT
    stream_lcd = _find_stream_lcd(stream_list)

    # DONE
    return stream_lcd


def _build_counter_obj(haystack: bytes | str, win_len: int) -> Counter:
    """Build and return a Counter() object."""
    return Counter(haystack[i:i+win_len] for i in range(len(haystack)-win_len+1))


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


def _find_lcd(stream1: bytes | str, stream2: bytes | str) -> bytes | str:
    """Find the leading least common preamble between two streams."""
    # LOCAL VARIABLES
    stream_lcd = stream1[:0]  # Working candidate for the lcd
    long_stream = stream1     # Longest stream, default starting condition
    shrt_stream = stream2     # Shortest stream, default starting condition

    # PREPARE
    if len(stream2) > len(stream1):
        long_stream = stream2
        shrt_stream = stream1

    # FIND IT
    for index in range(len(shrt_stream), 0, -1):
        if long_stream.startswith(shrt_stream[:index]):
            stream_lcd = shrt_stream[:index]  # Found it
            break  # Stop looking

    # DONE
    return stream_lcd


def _find_stream_lcd(stream_list: List[bytes | str]) -> bytes | str:
    """Find the leading common sub-string among a list of objects."""
    # LOCAL VARIABLES
    stream_lcd = stream_list[0]  # Working candidate for the lcd

    # FIND IT
    for next_stream in stream_list[1:]:
        stream_lcd = _find_lcd(next_stream, stream_lcd)

    # DONE
    return stream_lcd
