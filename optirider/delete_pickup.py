from optirider import setup
from optirider import start_day
from optirider.constants import WAIT_TIME_AT_WAREHOUSE, GLOBAL_END_TIME, MISS_PENALTY

# Delete pickup function will take data, tours and timings as parameter
# It will return tours, timings, changed_rider as result.
# tours will begin from data['tour_location'][vehicle_id] at current_time.
# The pickup at data['pickup_index'] will be deleted.
# changed_rider will be -1 if none rider's current tour is updated.
# pickup to be deleted must not be the next visiting location of any rider.


def delete_pickup(tours, timings, data):
    pickup = data["pickup_index"]
    num_vehicles = data["num_vehicles"]
    changed_tour = -1

    if "cur_time" not in data.keys():
        data["cur_time"] = GLOBAL_END_TIME

    for vehicle_id in range(num_vehicles):
        time_saved = -1
        for idx in range(
            data["tour_location"][vehicle_id] + 1, len(tours[vehicle_id][0])
        ):
            loc = tours[vehicle_id][0][idx]
            if loc == pickup:
                prev = tours[vehicle_id][0][idx - 1]
                next = tours[vehicle_id][0][idx + 1]

                time_saved = (
                    data["time_matrix"][prev][loc]
                    + data["time_matrix"][loc][next]
                    + data["service_time"][loc]
                    - data["time_matrix"][prev][next]
                )

                tours[vehicle_id][0].pop(idx)
                timings[vehicle_id][0].pop(idx)

                changed_tour = idx
                break

        if changed_tour != -1:
            for idx in range(changed_tour, len(tours[vehicle_id][0])):
                timings[vehicle_id][0][idx] -= time_saved

            for tour_id in range(1, len(tours[vehicle_id])):
                for loc in range(len(tours[vehicle_id][tour_id])):
                    timings[vehicle_id][tour_id][loc] -= time_saved

            changed_tour = vehicle_id
            break

    if changed_tour != -1:
        return tours, timings, changed_tour

    # Add all upcoming points except the pickup to the list and run start day function.
    points = []
    start_time = [GLOBAL_END_TIME for vechicle in range(num_vehicles)]

    for vehicle_id in range(num_vehicles):
        for v_tours in tours[vehicle_id]:
            for loc in v_tours:
                if loc > 0 and loc != pickup:
                    points.append(loc)
        try:
            start_time[vehicle_id] = timings[vehicle_id][0][-1] + WAIT_TIME_AT_WAREHOUSE
        except IndexError:
            start_time[vehicle_id] = data["cur_time"]

    upcoming_data = setup.extract_data(
        data, points, [vehicle_id for vehicle_id in range(num_vehicles)], start_time
    )
    drop_penalty = [MISS_PENALTY] * upcoming_data["num_locations"]

    upcoming_tour, upcoming_timings, _ = start_day.start_day(
        upcoming_data, drop_penalty
    )

    for vehicle_id in range(num_vehicles):
        for tour_id in range(len(upcoming_tour[vehicle_id])):
            upcoming_tour[vehicle_id][tour_id] = [
                points[idx] for idx in upcoming_tour[vehicle_id][tour_id]
            ]

        if len(tours[vehicle_id][0]) > 0:
            upcoming_tour[vehicle_id].insert(0, tours[vehicle_id][0])
            upcoming_timings[vehicle_id].insert(0, timings[vehicle_id][0])

    return upcoming_tour, upcoming_timings, changed_tour


# Consider case: Point 100 added, then 101 added, then 100 deleted. Now the 101 that was added should become the new 100
# This means that the data matrix that the function receives should not contain already deleted points.