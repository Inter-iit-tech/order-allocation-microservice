import numpy as np
from functools import partial
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from optirider.constants import MISS_PENALTY

from optirider import setup
from optirider import solution as optisolver

# import setup
# import solution as optisolver


def start_day(data, drop_penalty):
    tours = [[] for _ in range(data["num_vehicles"])]
    timings = [[] for _ in range(data["num_vehicles"])]
    total_penalty = 0
    if data["num_locations"] == 0:
        return tours, timings, total_penalty
    while True:
        # Create routing manager
        manager = pywrapcp.RoutingIndexManager(
            data["num_locations"], data["num_vehicles"], data["depot"]
        )

        # Create route model
        routing = pywrapcp.RoutingModel(manager)

        capacity_dimension_name = "Free Space"
        time_dimension_name = "Time"

        # Create volume evaluator, which gives the change in volume in transit
        volume_evaluator_index = routing.RegisterUnaryTransitCallback(
            partial(setup.create_volume_evaluator(data), manager)
        )

        # Adding the bag capacity constraint (hard constraint, should never be violated)
        setup.add_capacity_constraints(
            routing, data, volume_evaluator_index, capacity_dimension_name
        )

        # Adds time as the metric which model will try to minimize.
        transit_callback_index = routing.RegisterTransitCallback(
            partial(setup.gen_time_callback(data), manager)
        )
        # Set arc cost as time taken for travel.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Adds the constraint that different vechiles may start at different times (for further trips).
        setup.add_start_time_constraint(
            routing, data, transit_callback_index, time_dimension_name
        )

        # Adds expected delivery_time constriant (soft constraint, late delivery may happen, but that attracts penalty)
        setup.add_delivery_time_constraint(routing, manager, data, time_dimension_name)

        # Allow to drop nodes (in worst cases) Make penalty very high (greater than penalty for all late delivery combined)
        for drop_point in range(1, data["num_locations"]):
            routing.AddDisjunction(
                [manager.NodeToIndex(drop_point)], drop_penalty[drop_point]
            )

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            # print("Solution ends")
            break

        answer, timing, data, drop_penalty = optisolver.get_solution(
            data, manager, routing, solution, drop_penalty
        )

        # Cannot directly add, visited point may be added to miss penalty multiple times.
        total_penalty += solution.ObjectiveValue()

        # print(answer)
        vehicle_id = 0
        can_continue = 0
        for tour in answer:
            if len(tour) > 2:
                can_continue = 1
                timings[vehicle_id].append(timing[vehicle_id])
                # print(vehicle_id, tour)
                tours[vehicle_id].append(tour)
            vehicle_id += 1

        if max(drop_penalty) == 0 or can_continue == 0:
            # print("Solution ends")
            break

    # print(tours)
    # print(timings)
    return tours, timings, total_penalty


def main(option=1):
    data = setup.generate_data(option)
    drop_penalty = [MISS_PENALTY] * data["num_locations"]
    return start_day(data, drop_penalty)


if __name__ == "__main__":
    main(1)