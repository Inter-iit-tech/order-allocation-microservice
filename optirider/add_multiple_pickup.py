import math
import random
from functools import partial
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from optirider import setup
from optirider import start_day as optisolver

from optirider.constants import (
    MISS_PENALTY,
    WAIT_TIME_AT_WAREHOUSE,
    GLOBAL_END_TIME,
    CAPACITY_DIMENSION_NAME,
    TIME_DIMENSION_NAME,
)

# Can add multiple pickup.
# tours and timings are array of ongoing tour as well as upcoming tours, ongoing tour contains overall ongoing tour
#  with data['tour_location'][vehicle_id] giving us the next visit index of vehicle_id.
# If tour of any vehicle is empty give it as [[]] (one tour which is empty) rather than [] (no tour)
# If tour is empty for vehicle_id set data['tour_location'][vehicle_id] as -1

# Consider this: An order got missed in 1st trip, but delivered in 2nd, penalty will be biased in this case.
# The data matrix contains only those points starting from next delivery location for all vehicles or can contain all points ?


single_vehicle_vrp_default_runtime = 5
upcoming_tour_runtime = 10

def solve_constrained_vrp(
    tour_data, initial_tour, start_time, cur_time, cur_free_space, time_limit = single_vehicle_vrp_default_runtime
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
    setup.add_single_bag_capacity_constraint(
        routing,
        tour_data,
        volume_evaluator_index,
        CAPACITY_DIMENSION_NAME,
        cur_free_space,
    )

    # Adds time as the metric which model will try to minimize.
    transit_callback_index = routing.RegisterTransitCallback(
        partial(setup.gen_time_callback(tour_data), manager)
    )
    # Set arc cost as time taken for travel.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Adds the constraint that different vechiles may start at different times (for further trips).
    setup.add_single_start_time_constraint(
        routing,
        transit_callback_index,
        start_time,
        cur_time,
        TIME_DIMENSION_NAME,
    )

    # Adds expected delivery_time constriant (soft constraint, late delivery may happen, but that attracts penalty)
    setup.add_single_delivery_time_constraint(
        routing, manager, tour_data, TIME_DIMENSION_NAME
    )

    # Allow to drop nodes (in worst cases) Make penalty very high (greater than penalty for all late delivery combined)
    for drop_point in range(tour_data["num_locations"]):
        if drop_point != tour_data["end"][0]:
            routing.AddDisjunction(
                [manager.NodeToIndex(drop_point)], tour_data["penalty"][drop_point]
            )

    # Add constraint that the rider cannot visit more than tour_data['route_length'] locations
    def counter_callback(from_index):
        """Returns 1 for any locations except end."""
        # Convert from routing variable Index to user NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return 1 if (from_node != tour_data['end'][0]) else 0

    counter_callback_index = routing.RegisterUnaryTransitCallback(counter_callback)

    routing.AddDimension(
    counter_callback_index, 
    0, # No slack
    tour_data['route_length'], # Cannot exceed this
    True,   # Start from zero
    'Counter'
    )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.time_limit.seconds = time_limit

    routing.CloseModelWithParameters(search_parameters)

    # Get initial solution from routes after closing the model.
    initial_solution = routing.ReadAssignmentFromRoutes([initial_tour], True)

    solution = routing.SolveFromAssignmentWithParameters(
        initial_solution, search_parameters
    )

    # updated_tour, tour_timings, missed_point, start_time
    updated_tour = []
    missed_point = []
    tour_timings = []

    if not solution:
        print("No solution in vrp")
        missed_point = [points for points in range(1, tour_data["num_locations"])]
        return updated_tour, tour_timings, missed_point, start_time

    time_dimension = routing.GetDimensionOrDie(TIME_DIMENSION_NAME)

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
        start_time = solution.Value(curtime)

    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if solution.Value(routing.NextVar(node)) == node:
            missed_point.append(manager.IndexToNode(node))

    return updated_tour, tour_timings, missed_point, start_time


# Bug: Initial tour may be empty. (Handled)
# Run time issues: This function may take much time to run.


def add_pickup(tours, timings, data):

    if "cur_time" not in data.keys():
        data["cur_time"] = GLOBAL_END_TIME

    num_vehicles = len(tours)

    pickup_points = data["pickup_indices"]

    cur_day_delivery_penalty = data["penalty"][pickup_points[0]]

    # Set penalty of pickup indices as this.
    pickup_init_penalty = math.floor(
        (cur_day_delivery_penalty - 1) / len(pickup_points)
    )

    # All delivery points except depot
    further_points = []
    for vehicles in range(num_vehicles):
        for tour_no in range(1, len(tours[vehicles])):
            for order_no in tours[vehicles][tour_no]:
                if order_no != data["depot"]:
                    further_points.append(order_no)

        for current_order in tours[vehicles][0]:
            if current_order != data["depot"]:
                data["penalty"][current_order] = cur_day_delivery_penalty

    for pickup_point in pickup_points:
        data["penalty"][pickup_point] = pickup_init_penalty

    begin_next_journey_at = []
    for vehicle_id in range(num_vehicles):
        if data["tour_location"][vehicle_id] == -1:
            begin_next_journey_at.append(data['cur_time'])
        else:
            begin_next_journey_at.append(
                timings[vehicle_id][0][-1] + WAIT_TIME_AT_WAREHOUSE
            )

    vehicle_list_random = [_ for _ in range(num_vehicles)]
    random.shuffle(vehicle_list_random)

    current_tour = [[tours[vehicle][0]] for vehicle in range(num_vehicles)]
    current_timings = [[timings[vehicle][0]] for vehicle in range(num_vehicles)]

    for cnt_vehicle, vehicle_id in enumerate(vehicle_list_random):
        if len(pickup_points) == 0:
            break

        tour_idx = []
        start_idx = data["tour_location"][vehicle_id]
        cur_free_space = data["vehicle_capacity"][vehicle_id]

        start_time = data["cur_time"]

        initial_tour = []

        if start_idx == -1:
            start_idx = 0
            cur_time = data['cur_time']
        else:
            for i in range(start_idx, len(tours[vehicle_id][0])):
                if tours[vehicle_id][0][i] > 0:
                    tour_idx.append(tours[vehicle_id][0][i])
                    if i != start_idx:
                        initial_tour.append(len(tour_idx) - 1)
                    cur_free_space -= max(
                        data["package_volume"][tours[vehicle_id][0][i]], 0
                    )
            start_time = timings[vehicle_id][0][0]
            cur_time = timings[vehicle_id][0][start_idx]

        # This is the index of depot.
        tour_idx.append(0)
        end_idx = len(tour_idx) - 1

        for points in pickup_points:
            tour_idx.append(points)

        # Run vrp for points in tour_idx starting at tour_idx[0] and ending at tour_idx[len(tour_idx)-2]
        # Satisfying bag capacity constraint and that tour time may not exceed 4-5 hours or beyond 9 p.m. whichever lower.

        # Create data, here i will be tour_idx[i] location
        tour_data = setup.extract_data(data, tour_idx, [vehicle_id], [start_time])
        if start_idx == 0:
            tour_data["start"] = [end_idx]
        else:
            tour_data["start"] = [0]
        tour_data["end"] = [end_idx]

        rem_vehicles = num_vehicles - cnt_vehicle
        rem_pickups = len(pickup_points)

        expected_pickup_per_rider = math.ceil(rem_vehicles/rem_pickups)
        tour_data['route_length'] = len(initial_tour) + 1 + expected_pickup_per_rider + 2

        (updated_tour, tour_timings, missed_point, start_time,) = solve_constrained_vrp(
            tour_data, initial_tour, start_time, cur_time, cur_free_space
        )

        begin_next_journey_at[vehicle_id] = start_time + WAIT_TIME_AT_WAREHOUSE

        current_tour[vehicle_id][0] = [
            tours[vehicle_id][0][i] for i in range(start_idx)
        ]
        current_timings[vehicle_id][0] = [
            timings[vehicle_id][0][i] for i in range(start_idx)
        ]

        for loc_id, loc in enumerate(updated_tour):
            current_tour[vehicle_id][0].append(tour_idx[loc])
            current_timings[vehicle_id][0].append(tour_timings[loc_id])

        pickup_points = []
        for point in missed_point:
            order_id = tour_idx[point]
            if data["package_volume"][order_id] > 0:  # Delivery order
                further_points.append(order_id)
            else:  # Pickup order
                pickup_points.append(order_id)

    # Make penalty of pickup equal to cur_day_delivery penalty for upcoming penalty.
    for points in pickup_points:
        further_points.append(points)
        data["penalty"][points] = cur_day_delivery_penalty

    further_points.insert(0, 0)

    upcoming_tour_data = setup.extract_data(
        data,
        further_points,
        [vehicle_id for vehicle_id in range(num_vehicles)],
        begin_next_journey_at,
    )

    # Update the time for which algo will run and see if guided local search is required or not.
    # Integrate miss penalty into data only.
    upcoming_tour, upcoming_time, upcoming_penalty = optisolver.start_day(
        upcoming_tour_data, [MISS_PENALTY] * upcoming_tour_data["num_locations"], upcoming_tour_runtime
    )

    total_tour = [element for element in current_tour]
    total_timings = [element for element in current_timings]
    for vehicle in range(num_vehicles):
        if len(total_tour[vehicle][0]) == 0:
            total_tour[vehicle].pop(0)
            total_timings[vehicle].pop(0)
        for trip_idx in range(len(upcoming_tour[vehicle])):
            total_tour[vehicle].append(
                [further_points[loc] for loc in upcoming_tour[vehicle][trip_idx]]
            )
            total_timings[vehicle].append(
                [time for time in upcoming_time[vehicle][trip_idx]]
            )

    return total_tour, total_timings


if __name__ == "__main__":
    tours, timings, _ = optisolver.main()
    data = setup.get_updated_data()

    add_pickup(tours, timings, data)
