from datetime import datetime, timedelta
from typing import List, Tuple


def find_common_slots(
    availability_windows: List[List[Tuple[datetime, datetime]]],
    duration_minutes: int
) -> List[Tuple[datetime, datetime]]:

    if not availability_windows:
        return []

    common_slots = availability_windows[0]

    for participant_slots in availability_windows[1:]:
        new_common_slots = []

        for start_a, end_a in common_slots:
            for start_b, end_b in participant_slots:

                common_start = max(start_a, start_b)
                common_end = min(end_a, end_b)

                if common_start < common_end:
                    new_common_slots.append(
                        (common_start, common_end)
                    )

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