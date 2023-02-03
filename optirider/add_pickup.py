import numpy as np
from functools import partial
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from optirider import setup
from optirider import start_day as optisolver


from optirider.constants import (
    MISS_PENALTY,
    WAIT_TIME_AT_WAREHOUSE,
    GLOBAL_END_TIME,
)

# Can add a single pickup at once.
# tours and timings are array of ongoing tour as well as upcoming tours, ongoing tour contains overall ongoing tour
#  with data['tour_location'][vehicle_id] giving us the next visit index of vehicle_id.
# If tour of any vehicle is empty give it as [[]] (one tour which is empty) rather than [] (no tour)
# If tour is empty for vehicle_id set data['tour_location'][vehicle_id] as -1

# Consider this: An order got missed in 1st trip, but delivered in 2nd, penalty will be biased in this case.
# The data matrix contains only those points starting from next delivery location for all vehicles or can contain all points ?


def solve_constrained_vrp(
    tour_data, start_time, cur_time, cur_free_space, time_limit=10
):
    # Create routing manager (with different start and end location)
    manager = pywrapcp.RoutingIndexManager(
        tour_data["num_locations"],
        tour_data["num_vehicles"],
        tour_data["start"],
        tour_data["end"],
    )

    routing = pywrapcp.RoutingModel(manager)
    # Add bag capacity constraint
    # Step - 1: Create volume evaluator, which gives the change in volume in transit
    volume_evaluator_index = routing.RegisterUnaryTransitCallback(
        partial(setup.create_volume_evaluator(tour_data), manager)
    )
    # Step-2: Create dimension and add constraint for single vehicle
    capacity_dimension_name = "Free Space"
    setup.add_single_bag_capacity_constraint(
        routing,
        tour_data,
        volume_evaluator_index,
        capacity_dimension_name,
        cur_free_space,
    )

    # Adds time as the metric which model will try to minimize.
    transit_callback_index = routing.RegisterTransitCallback(
        partial(setup.gen_time_callback(tour_data), manager)
    )
    # Set arc cost as time taken for travel.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Adds the constraint that different vechiles may start at different times (for further trips).
    time_dimension_name = "Time"
    setup.add_single_start_time_constraint(
        routing,
        tour_data,
        transit_callback_index,
        start_time,
        cur_time,
        time_dimension_name,
    )

    # Adds expected delivery_time constriant (soft constraint, late delivery may happen, but that attracts penalty)
    setup.add_single_delivery_time_constraint(
        routing, manager, tour_data, time_dimension_name
    )

    # Allow to drop nodes (in worst cases) Make penalty very high (greater than penalty for all late delivery combined)
    for drop_point in range(tour_data["num_locations"]):
        if drop_point != tour_data["end"][0]:
            routing.AddDisjunction([manager.NodeToIndex(drop_point)], MISS_PENALTY)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.time_limit.seconds = time_limit

    solution = routing.SolveWithParameters(search_parameters)

    # updated_tour, tour_timings, missed_point, start_time
    updated_tour = []
    missed_point = []
    tour_timings = []

    if not solution:
        print("No solution in vrp")
        return updated_tour, tour_timings, missed_point, start_time

    penalty = solution.ObjectiveValue()
    time_dimension = routing.GetDimensionOrDie(time_dimension_name)

    for vehicle_id in range(tour_data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        while not routing.IsEnd(index):
            updated_tour.append(manager.IndexToNode(index))
            curtime = time_dimension.CumulVar(index)
            tour_timings.append(solution.Value(curtime))
            index = solution.Value(routing.NextVar(index))

        updated_tour.append(manager.IndexToNode(index))
        curtime = time_dimension.CumulVar(index)
        tour_timings.append(solution.Value(curtime))

        # wait time at warehouse is taken care by function which calls this.
        start_time = cur_time

    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if solution.Value(routing.NextVar(node)) == node:
            missed_point.append(manager.IndexToNode(node))

    # print(updated_tour, missed_point, start_time, penalty)

    return updated_tour, tour_timings, missed_point, start_time


def add_pickup(tours, timings, data):

    num_vehicles = len(tours)

    updated_tours = tours
    upcoming_timings = timings
    changed_rider = -1
    # Miss penalty is added corresponding to the newly added pickup point.
    cur_min_penalty = setup.get_penalty(tours, timings, data) + MISS_PENALTY

    for vehicle_id in range(num_vehicles + 1):
        if vehicle_id < num_vehicles and data["tour_location"][vehicle_id] == -1:
            continue
        temp_tours = [[tours[vehicle][0]] for vehicle in range(num_vehicles)]
        temp_timings = [[timings[vehicle][0]] for vehicle in range(num_vehicles)]

        begin_at = [[] for id in range(num_vehicles)]
        missed_point = []
        penalty = 0

        for vehicles in range(num_vehicles):
            try:
                begin_at[vehicles] = timings[vehicles][0][-1] + WAIT_TIME_AT_WAREHOUSE
            except IndexError:
                # NOTE: This can be improved. If a vehicle does not have route at current time, this means it's start time
                # can be cur_time + WAIT_TIME_AT_WAREHOUSE in worst case.
                begin_at[vehicles] = GLOBAL_END_TIME

        if vehicle_id < num_vehicles:
            tour_idx = []
            start_idx = data["tour_location"][vehicle_id]
            cur_free_space = data["vehicle_capacity"][vehicle_id]
            for i in range(start_idx, len(tours[vehicle_id][0])):
                tour_idx.append(tours[vehicle_id][0][i])
                cur_free_space -= max(
                    data["package_volume"][tours[vehicle_id][0][i]], 0
                )
            tour_idx.append(data["pickup_index"])
            start_time = timings[vehicle_id][0][0]
            cur_time = (
                timings[vehicle_id][0][start_idx]
                + data["service_time"][tours[vehicle_id][0][start_idx]]
            )
            # capacity = data['vehicle_capacity'][vehicle_id]
            # Run vrp for points in tour_idx starting at tour_idx[0] and ending at tour_idx[len(tour_idx)-2]
            # Satisfying bag capacity constraint and that tour time may not exceed 4-5 hours or beyond 9 p.m. whichever lower.

            # Create data, here i will be tour_idx[i] location
            tour_data = setup.extract_data(data, tour_idx, [vehicle_id], [start_time])
            tour_data["start"] = [0]
            tour_data["end"] = [len(tour_idx) - 2]

            # updated_tours[vehicle_id]
            (
                updated_tour,
                tour_timings,
                missed_point,
                start_time,
            ) = solve_constrained_vrp(tour_data, start_time, cur_time, cur_free_space)
            start_time += WAIT_TIME_AT_WAREHOUSE

            temp_tours[vehicle_id][0] = [
                tours[vehicle_id][0][i] for i in range(start_idx)
            ]

            temp_timings[vehicle_id][0] = [
                tours[vehicle_id][0][i] for i in range(start_idx)
            ]

            for loc_id, loc in enumerate(updated_tour):
                temp_tours[vehicle_id][0].append(tour_idx[loc])
                temp_timings[vehicle_id][0].append(tour_timings[loc_id])
            begin_at[vehicle_id] = start_time
        else:
            missed_point.append(data["pickup_index"])
            # Calculate penalty (late time and time_taken) - Now incorrectly calculated.
            # prev_order = -1
            # for vehicle in range(num_vehicles):
            #     if data['tour_location'][vehicle] == -1:
            #         continue
            #     for i in range(data["tour_location"][vehicle], len(temp_tours[vehicle][0])):
            #         order = temp_tours[vehicle][0][i]
            #         penalty += setup.late_penalty_add(
            #             temp_timings[vehicle][0][i] - data["delivery_time"][order]
            #         )
            #         if prev_order != -1:
            #             penalty = data["time_matrix"][prev_order][order]
            #         prev_order = order
        for vehicle in range(num_vehicles):
            if data["tour_location"][vehicle] == -1:
                continue
            prev_order = -1
            for i in range(len(temp_tours[vehicle][0])):
                order = temp_tours[vehicle][0][i]
                if order > 0:
                    penalty += setup.late_penalty_add(
                        temp_timings[vehicle][0][i] - data["delivery_time"][order]
                    )
                if prev_order != -1:
                    penalty += data["time_matrix"][prev_order][order]
                prev_order = order

        for vehicles in range(num_vehicles):
            for tour_no in range(1, len(tours[vehicles])):
                for order_no in tours[vehicles][tour_no]:
                    if order_no != data["depot"]:
                        missed_point.append(order_no)

        # Ensures that depot is at location 0
        missed_point.insert(0, 0)

        # Run algorithm for upcoming tour
        upcoming_tour_data = setup.extract_data(
            data, missed_point, [i for i in range(num_vehicles)], begin_at
        )

        upcoming_tour, upcoming_time, upcoming_penalty = optisolver.start_day(
            upcoming_tour_data, [MISS_PENALTY] * upcoming_tour_data["num_locations"], 60
        )

        upcoming_penalty = 0
        cnt_miss_delivery = len(missed_point) - 1

        for vehicle in range(upcoming_tour_data["num_vehicles"]):
            for trip_idx in range(len(upcoming_tour[vehicle])):
                temp_tours[vehicle].append(
                    [missed_point[loc] for loc in upcoming_tour[vehicle][trip_idx]]
                )
                temp_timings[vehicle].append(
                    [time for time in upcoming_time[vehicle][trip_idx]]
                )
                prev_order = -1
                for idx in range(len(upcoming_tour[vehicle][trip_idx])):
                    order = upcoming_tour[vehicle][trip_idx][idx]
                    order = missed_point[order]
                    if order > 0:
                        upcoming_penalty += setup.late_penalty_add(
                            upcoming_time[vehicle][trip_idx][idx]
                            - data["delivery_time"][order]
                        )
                        cnt_miss_delivery -= 1
                    if prev_order != -1:
                        upcoming_penalty += data["time_matrix"][prev_order][order]
                    prev_order = order

        upcoming_penalty += cnt_miss_delivery * MISS_PENALTY

        if upcoming_penalty + penalty < cur_min_penalty:
            cur_min_penalty = upcoming_penalty + penalty
            updated_tours = temp_tours
            upcoming_timings = temp_timings
            changed_rider = vehicle_id

    if changed_rider == num_vehicles:
        changed_rider = -1
    return updated_tours, upcoming_timings, changed_rider


if __name__ == "__main__":
    tours, timings, _ = optisolver.main()
    data = setup.get_updated_data()

    add_pickup(tours, timings, data)

# tour_data = {'time_matrix': [[0, 3209, 2611], [3209, 0, 4173], [2611, 4173, 0]], 'num_locations': 3, 'num_vehicles': 1, 'depot': 0, 'vehicle_capacity': [
#     240], 'start_time': [32400], 'delivery_time': [72327, 0, 54234], 'package_volume': [24, 0, -28], 'service_time': [300, 0, 300], 'start': [0], 'end': [1]}
# print(solve_constrained_vrp(tour_data, 32400, 45007, 240-24))
