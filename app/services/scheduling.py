from datetime import datetime, timedelta
from typing import List, Tuple


def find_common_slots(
    availability_windows: List[List[Tuple[datetime, datetime]]],
    duration_minutes: int
) -> List[Tuple[datetime, datetime]]:

    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero")

    if not availability_windows:
        return []

    common_slots = _merge_intervals(availability_windows[0])

    for participant_slots in availability_windows[1:]:
        new_common_slots = []
        participant_slots = _merge_intervals(participant_slots)
        common_index = 0
        participant_index = 0

        while (common_index < len(common_slots)
               and participant_index < len(participant_slots)):
            start_a, end_a = common_slots[common_index]
            start_b, end_b = participant_slots[participant_index]
            common_start = max(start_a, start_b)
            common_end = min(end_a, end_b)

            if common_start < common_end:
                new_common_slots.append((common_start, common_end))

            if end_a <= end_b:
                common_index += 1
            if end_b <= end_a:
                participant_index += 1

        common_slots = new_common_slots

    duration = timedelta(minutes=duration_minutes)

    valid_slots = []

    for start, end in common_slots:
        current_start = start

        while current_start + duration <= end:
            current_end = current_start + duration

            valid_slots.append(
                (current_start, current_end)
            )

            current_start += duration

    return valid_slots


def _merge_intervals(
    intervals: List[Tuple[datetime, datetime]]
) -> List[Tuple[datetime, datetime]]:
    merged = []

    for start, end in sorted(intervals):
        if start >= end:
            continue

        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))

    return merged