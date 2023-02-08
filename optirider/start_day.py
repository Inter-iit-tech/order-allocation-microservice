import math
from functools import partial
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from optirider.constants import (
    MISS_PENALTY,
    TIME_DIMENSION_NAME,
    CAPACITY_DIMENSION_NAME,
    DEFAULT_TIME_LIMIT,
)

from optirider import setup
from optirider import solution as optisolver


def start_day(data, drop_penalty, time_to_limit=DEFAULT_TIME_LIMIT):
    tours = [[] for _ in range(data["num_vehicles"])]
    timings = [[] for _ in range(data["num_vehicles"])]

    # time_to_limit = 300
    print("HELLO")

    total_penalty = 0
    points_to_map = [loc for loc in range(data["num_locations"])]

    drop_penalty = [penalty for penalty in data["penalty"]]

    if data["num_locations"] == 0:
        return tours, timings, total_penalty

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    solution_strategy = "PATH_CHEAPEST_ARC"
    if "first_solution_strategy" in data.keys():
        solution_strategy = data["first_solution_strategy"]

    search_parameters.first_solution_strategy = getattr(
        routing_enums_pb2.FirstSolutionStrategy, solution_strategy
    )
    if "local_search_metaheuristic" in data:
        search_parameters.local_search_metaheuristic = data[
            "local_search_metaheuristic"
        ]

    # Logic_0: Distrubute the time_to_limit among all iteration uniformly.
    expected_loops = math.ceil(
        sum(max(loads, 0) for loads in data["package_volume"])
        / sum(capacity for capacity in data["vehicle_capacity"])
    )
    expected_loops = max(1, expected_loops)
    search_parameters.time_limit.seconds = math.ceil(time_to_limit / (expected_loops))

    while True:
        # Create routing manager
        manager = pywrapcp.RoutingIndexManager(
            data["num_locations"], data["num_vehicles"], data["depot"]
        )

        # Create route model
        routing = pywrapcp.RoutingModel(manager)

        # Create volume evaluator, which gives the change in volume in transit
        volume_evaluator_index = routing.RegisterUnaryTransitCallback(
            partial(setup.create_volume_evaluator(data), manager)
        )

        # Adding the bag capacity constraint (hard constraint, should never be violated)
        setup.add_capacity_constraints(
            routing, data, volume_evaluator_index, CAPACITY_DIMENSION_NAME
        )

        # Adds time as the metric which model will try to minimize.
        transit_callback_index = routing.RegisterTransitCallback(
            partial(setup.gen_time_callback(data), manager)
        )

        # Set arc cost as time taken for travel.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Adds the constraint that different vechiles may start at different times (for further trips).
        setup.add_start_time_constraint(
            routing, data, transit_callback_index, TIME_DIMENSION_NAME
        )

        # Adds expected delivery_time constriant (soft constraint, late delivery may happen, but that attracts penalty)
        setup.add_delivery_time_constraint(routing, manager, data, TIME_DIMENSION_NAME)

        # Allow to drop nodes (in worst cases) Make penalty very high (greater than penalty for all late delivery combined)
        for drop_point in range(1, data["num_locations"]):
            routing.AddDisjunction(
                [manager.NodeToIndex(drop_point)], drop_penalty[drop_point]
            )

        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            break

        answer, timing, data, drop_penalty = optisolver.get_solution(
            data, manager, routing, solution, drop_penalty
        )

        new_points_to_map = [loc for loc in range(data["num_locations"])]
        points_to_take = [0]

        new_drop_penalty = []
        for location_idx, penalty in enumerate(drop_penalty):
            if penalty > 0:
                new_points_to_map[len(points_to_take)] = points_to_map[location_idx]
                points_to_take.append(location_idx)
                new_drop_penalty.append(penalty)

        drop_penalty = [new_miss_penalty for new_miss_penalty in new_drop_penalty]
        data = setup.extract_data(
            data,
            points_to_take,
            [vehicle_id for vehicle_id in range(data["num_vehicles"])],
            data["start_time"],
        )

        # Cannot directly add, visited point may be added to miss penalty multiple times.
        # total_penalty += solution.ObjectiveValue()

        vehicle_id = 0
        can_continue = 0
        for tour in answer:
            if len(tour) > 2:
                can_continue = 1
                timings[vehicle_id].append(timing[vehicle_id])

                actual_tour = [points_to_map[loc] for loc in tour]
                tours[vehicle_id].append(actual_tour)

            vehicle_id += 1

        points_to_map = new_points_to_map
        if len(drop_penalty) == 0 or max(drop_penalty) == 0 or can_continue == 0:
            break

    # total penalty will always be zero.
    return tours, timings, total_penalty


def main(option=1):
    data = setup.generate_data(option)
    drop_penalty = [MISS_PENALTY] * data["num_locations"]
    return start_day(data, drop_penalty)


if __name__ == "__main__":
    main(1)
