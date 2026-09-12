from typing import List, Tuple

def get_spread_offsets(spread_type: str, spread_range: int) -> List[Tuple[int, int]]:
    """
    Returns relative (d_row, d_col) coordinate offsets for a given spread type and range.
    """
    offsets = []
    st = spread_type.lower().replace("_", "").replace("-", "")

    if st == "vonneumann":
        # 4-directional Manhattan distance <= range
        for dr in range(-spread_range, spread_range + 1):
            for dc in range(-spread_range, spread_range + 1):
                if 0 < abs(dr) + abs(dc) <= spread_range:
                    offsets.append((dr, dc))

    elif st == "moore":
        # 8-directional Chebyshev distance <= range
        for dr in range(-spread_range, spread_range + 1):
            for dc in range(-spread_range, spread_range + 1):
                if 0 < max(abs(dr), abs(dc)) <= spread_range:
                    offsets.append((dr, dc))

    elif st == "row":
        # Linear along row (horizontal: same row, varying col)
        for dc in range(-spread_range, spread_range + 1):
            if dc != 0:
                offsets.append((0, dc))

    elif st == "column":
        # Linear along col (vertical: same col, varying row)
        for dr in range(-spread_range, spread_range + 1):
            if dr != 0:
                offsets.append((dr, 0))

    elif st == "crosshatch":
        # Diagonal multi-axis / cross-hatch pattern (dr == dc or dr == -dc)
        for d in range(1, spread_range + 1):
            offsets.extend([(d, d), (d, -d), (-d, d), (-d, -d)])

    else:
        # Default fallback to VonNeumann
        for dr in range(-spread_range, spread_range + 1):
            for dc in range(-spread_range, spread_range + 1):
                if 0 < abs(dr) + abs(dc) <= spread_range:
                    offsets.append((dr, dc))

    return offsets

def get_shade_offsets(radius: int) -> List[Tuple[int, int]]:
    """
    Returns Chebyshev / circular offsets within radius r for shade casting.
    """
    offsets = []
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            if 0 < max(abs(dr), abs(dc)) <= radius:
                offsets.append((dr, dc))
    return offsets

