"""Functionality to analyze data."""

# Standard Imports
from collections import defaultdict
# Third Party Imports
# Local Imports


def find_common_repeats(haystack: bytes | str, win_len: int = 24,
                        max_num: int = 1) -> List[tuple[bytes|str:int]]:
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


def find_dense_repeat(haystack: bytes | str) -> tuple[bytes|str:int]:
    """Find the most reaping substring (count(substring) * len(subsring)) in the haystack.

    The substring will always be longer than a single character.

    Args:
        haystack: The object to search for repeating strings.

    Returns:
        The first occurrence of the most dense substring in the haystack.
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
        repeats += find_common_repeats(haystack, win_len, max_num)
    # Set a benchmark to compare the rest of the results against
    dense_repeat = repeats[0]  # This is the 
    cur_winner = len(dense_repeat[0]) * dense_repeat[1]
    # Check for values that exceed the current benchmark
    for repeat in repeats:
        temp_density = len(repeat[0]) * repeat[1]
        if temp_density > cur_winner:
            dense_repeat = repeat  # Current record holder for "most dense repeat"
            cur_winner = temp_density  # New record to beat

    # DONE
    return dense_repeat


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
    result = {key:value for key,value in seen.items() if len(value) > 1}

    # DONE
    return result


def _build_counter_obj(haystack: bytes | str, win_len: int) -> Counter:
    """Build and return a Counter() object."""
    return Counter(haystack[i:i+win_len] for i in range(len(haystack)-win_len+1))
