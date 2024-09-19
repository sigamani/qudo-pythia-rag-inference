from typing import List, Tuple


def deduplicate_list_tuple(lst: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen = set()
    return [(a, b) for a, b in lst if not (a in seen or seen.add(a))]


def difference_list_tuple(lst1: List[Tuple[str, str]], lst2: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    seen = set([a for a, b in lst2])
    return [(a, b) for a, b in lst1 if a not in seen]