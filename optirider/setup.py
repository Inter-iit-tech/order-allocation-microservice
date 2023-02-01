import numpy as np

from optirider.constants import (
    LATE_DELIVERY_PENALTY_PER_SEC,
    MAX_TRIP_TIME,
    GLOBAL_END_TIME,
)


def create_data_model(
    time_matrix,
    capacity,
    start_time,
    service_time,
    package_volume,
    delivery_time,
    num_vehicles=1,
    depot=0,
):
    """Arranges data for passing to OR Tools.

    :param time_matrix: Adjacency matrix of all the nodes
    :param capacity: Capacity of vehiles
    :param start_time: Global time at which vehicle can start from warehouse.
    :param service_time: Time spent by rider at each location.
    :param package_volume: Volume of each package.
    :param delivery_time: Global time of expected delivery_time.
    :param int num_vehicles: Number of riders available to deliver.
    :param int depot: Index of depot (defaults to 0)
    :returns: A dictionary with all the data properly arranged
    """
    data = {
        "time_matrix": np.array(time_matrix),
        "num_locations": len(time_matrix),
        "num_vehicles": num_vehicles,
        "depot": depot,
        "package_volume": package_volume,
        "vehicle_capacity": capacity,
        "start_time": start_time,
        # Note: service_time at depot should be kept zero.
        "service_time": service_time,
        "delivery_time": delivery_time,
    }
    return data


def generate_data(option):
    return create_data_model(
        np.array(
            # fmt: off
            [
                [0, 548, 776, 696, 582, 274, 502, 194, 308,
                    194, 536, 502, 388, 354, 468, 776, 662],
                [548, 0, 684, 308, 194, 502, 730, 354, 696,
                    742, 1084, 594, 480, 674, 1016, 868, 1210],
                [776, 684, 0, 992, 878, 502, 274, 810, 468,
                    742, 400, 1278, 1164, 1130, 788, 1552, 754],
                [696, 308, 992, 0, 114, 650, 878, 502, 844,
                    890, 1232, 514, 628, 822, 1164, 560, 1358],
                [582, 194, 878, 114, 0, 536, 764, 388, 730,
                    776, 1118, 400, 514, 708, 1050, 674, 1244],
                [274, 502, 502, 650, 536, 0, 228, 308, 194,
                    240, 582, 776, 662, 628, 514, 1050, 708],
                [502, 730, 274, 878, 764, 228, 0, 536, 194,
                    468, 354, 1004, 890, 856, 514, 1278, 480],
                [194, 354, 810, 502, 388, 308, 536, 0, 342,
                    388, 730, 468, 354, 320, 662, 742, 856],
                [308, 696, 468, 844, 730, 194, 194, 342, 0,
                    274, 388, 810, 696, 662, 320, 1084, 514],
                [194, 742, 742, 890, 776, 240, 468, 388, 274,
                    0, 342, 536, 422, 388, 274, 810, 468],
                [536, 1084, 400, 1232, 1118, 582, 354, 730,
                    388, 342, 0, 878, 764, 730, 388, 1152, 354],
                [502, 594, 1278, 514, 400, 776, 1004, 468,
                    810, 536, 878, 0, 114, 308, 650, 274, 844],
                [388, 480, 1164, 628, 514, 662, 890, 354, 696,
                    422, 764, 114, 0, 194, 536, 388, 730],
                [354, 674, 1130, 822, 708, 628, 856, 320, 662,
                    388, 730, 308, 194, 0, 342, 422, 536],
                [468, 1016, 788, 1164, 1050, 514, 514, 662,
                    320, 274, 388, 650, 536, 342, 0, 764, 194],
                [776, 868, 1552, 560, 674, 1050, 1278, 742,
                    1084, 810, 1152, 274, 388, 422, 764, 0, 798],
                [662, 1210, 754, 1358, 1244, 708, 480, 856,
                    514, 468, 354, 844, 730, 536, 194, 798, 0],
            ]
            # fmt: on
        ),
        capacity=np.array([40, 50, 50, 50]),  # capacity
        start_time=np.array(
            [3600 * 9, 3600 * 9 + 1000, 3600 * 9, 3600 * 9]
        ),  # start_time
        service_time=np.full(17, 0),  # service_time
        package_volume=np.full(17, 10),  # package_volume
        delivery_time=np.full(17, 33500),  # delivery_time
        num_vehicles=4,
    )


def gen_time_callback(data):
    """Generates time callback from tour data and node.

    :param data: Data, as arranged by :ref:`create_data_model`
    :param ortools.constraint_solver.pywrapcp.RoutingIndexManager manager: Node manager
    :param ortools.constraint_solver.pywrapcp.RoutingModel routing: OR Tools routing model
    :returns: The index of callback in routing model
    """

    def time_callback(manager, from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["time_matrix"][from_node][to_node] + data["service_time"][from_node]

    # transit_callback_index = routing.RegisterTransitCallback(time_callback)
    # routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    return time_callback


def create_volume_evaluator(data):
    """Creates callback to get package_volume at each locations."""
    volume = data["package_volume"]

    def volume_evaluator(manager, node):
        """Returns the volume to be delivered at current node"""
        return volume[manager.IndexToNode(node)]

    return volume_evaluator


def add_capacity_constraints(
    routing, data, volume_evaluator_index, capacity_dimension_name
):
    """Adds capacity constraint"""
    routing.AddDimensionWithVehicleCapacity(
        # Gives the transit value (change) when travelling from i.
        volume_evaluator_index,
        0,  # Cannot overflow the bag.
        # This is the array of max_free_space available.
        data["vehicle_capacity"],
        # No need to for free_space to be zero initially.
        False,
        capacity_dimension_name,
    )


# Handle service time where? (used gen_time_callback at ArcCostEvaluator)


def add_start_time_constraint(routing, data, time_evaluator_index, time_dimension_name):

    trip_end_time = [
        min(GLOBAL_END_TIME, start_time + MAX_TRIP_TIME)
        for start_time in data["start_time"]
    ]
    routing.AddDimensionWithVehicleCapacity(
        time_evaluator_index,
        0,  # Does not allow waiting time.
        trip_end_time,  # Global maximum time for a vehicle.
        False,  # Time will not start from 0.
        time_dimension_name,
    )
    time_dimension = routing.GetDimensionOrDie(time_dimension_name)

    # Add start time for each vehicle.
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        x = int(data["start_time"][vehicle_id])  # Convert to int type
        # print(vehicle_id, x)
        time_dimension.CumulVar(index).SetRange(x, x)


def add_delivery_time_constraint(routing, manager, data, time_dimension_name):
    time_dimension = routing.GetDimensionOrDie(time_dimension_name)
    for location_idx, delivery_time in enumerate(data["delivery_time"]):
        if location_idx == data["depot"]:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.SetCumulVarSoftUpperBound(
            index, int(delivery_time), LATE_DELIVERY_PENALTY_PER_SEC
        )


def add_global_dimension(routing, callback_index, dim_name, slack, capacity, coeff):
    """Adds a dimension in the routing model

    :param ortools.constraint_solver.pywrapcp.RoutingModel routing: OR Tools routing model
    :param int callback_index: callback index
    :param str dim_name: name of the dimension
    :param int slack: slack for the dimension
    :param int capacity: maximum permitted value for each rider
    :param int coeff: global cost coefficient
    """
    routing.AddDimension(callback_index, slack, capacity, True, dim_name)
    dimension = routing.GetDimensionOrDie(dim_name)
    dimension.SetGlobalSpanCostCoefficient(coeff)


def create_updated_data(
    time_matrix,
    tour_location,
    depot,
    pickup_index,
    service_time,
    package_volume,
    delivery_time,
    capacity,
):
    data = {
        "time_matrix": time_matrix,
        "num_locations": len(time_matrix),
        "num_vehicles": len(capacity),
        "depot": depot,
        "tour_location": tour_location,
        "pickup_index": pickup_index,
        "service_time": service_time,
        "package_volume": package_volume,
        "delivery_time": delivery_time,
        "capacity": capacity,
    }
    return data


def get_updated_data():
    package_volume = np.full(18, 10)
    package_volume[17] = -10  # As it is a pickup

    service_time = np.full(18, 0)
    delivery_time = np.full(18, 33500)

    return create_updated_data(
        np.array(
            # fmt: off
            [
                [0, 548, 776, 696, 582, 274, 502, 194, 308,
                    194, 536, 502, 388, 354, 468, 776, 662, 1200],
                [548, 0, 684, 308, 194, 502, 730, 354, 696,
                    742, 1084, 594, 480, 674, 1016, 868, 1210, 1230],
                [776, 684, 0, 992, 878, 502, 274, 810, 468,
                    742, 400, 1278, 1164, 1130, 788, 1552, 754, 432],
                [696, 308, 992, 0, 114, 650, 878, 502, 844,
                    890, 1232, 514, 628, 822, 1164, 560, 1358, 532],
                [582, 194, 878, 114, 0, 536, 764, 388, 730,
                    776, 1118, 400, 514, 708, 1050, 674, 1244, 921],
                [274, 502, 502, 650, 536, 0, 228, 308, 194,
                    240, 582, 776, 662, 628, 514, 1050, 708, 965],
                [502, 730, 274, 878, 764, 228, 0, 536, 194,
                    468, 354, 1004, 890, 856, 514, 1278, 480, 354],
                [194, 354, 810, 502, 388, 308, 536, 0, 342,
                    388, 730, 468, 354, 320, 662, 742, 856, 1069],
                [308, 696, 468, 844, 730, 194, 194, 342, 0,
                    274, 388, 810, 696, 662, 320, 1084, 514, 679],
                [194, 742, 742, 890, 776, 240, 468, 388, 274,
                    0, 342, 536, 422, 388, 274, 810, 468, 845],
                [536, 1084, 400, 1232, 1118, 582, 354, 730,
                    388, 342, 0, 878, 764, 730, 388, 1152, 354, 1256],
                [502, 594, 1278, 514, 400, 776, 1004, 468,
                    810, 536, 878, 0, 114, 308, 650, 274, 844, 556],
                [388, 480, 1164, 628, 514, 662, 890, 354, 696,
                    422, 764, 114, 0, 194, 536, 388, 730, 664],
                [354, 674, 1130, 822, 708, 628, 856, 320, 662,
                    388, 730, 308, 194, 0, 342, 422, 536, 463],
                [468, 1016, 788, 1164, 1050, 514, 514, 662,
                    320, 274, 388, 650, 536, 342, 0, 764, 194, 967],
                [776, 868, 1552, 560, 674, 1050, 1278, 742,
                    1084, 810, 1152, 274, 388, 422, 764, 0, 798, 1300],
                [662, 1210, 754, 1358, 1244, 708, 480, 856,
                    514, 468, 354, 844, 730, 536, 194, 798, 0, 750],
                [1200, 1230, 432, 532, 921, 965, 354, 1069,
                    679, 845, 1256, 556, 664, 463, 967, 1300, 750, 0]
            ]
            # fmt: on
        ),
        tour_location=[1, 1, 1, 1],  # location of all vehicles in tour.
        pickup_index=17,
        depot=0,
        service_time=service_time,  # service_time
        package_volume=package_volume,  # package_volume
        delivery_time=delivery_time,  # delivery_time
        capacity=np.array([40, 50, 50, 50]),  # capacity
    )


def add_single_bag_capacity_constraint(
    routing, data, volume_evaluator_index, capacity_dimension_name, initial_free
):
    routing.AddDimension(
        # Gives the transit value (change) when travelling from i.
        volume_evaluator_index,
        0,  # Cannot overflow the bag.
        # This is max_free_space available.
        int(data["vehicle_capacity"][0]),
        # No need to for free_space to be zero initially.
        False,
        capacity_dimension_name,
    )
    capacity_dimension = routing.GetDimensionOrDie(capacity_dimension_name)
    # Set the initial free space
    capacity_dimension.CumulVar(routing.Start(0)).SetValue(int(initial_free))


def add_single_start_time_constraint(
    routing, data, time_evaluator_index, start_time, cur_time, time_dimension_name
):
    trip_end_time = min(GLOBAL_END_TIME, start_time + MAX_TRIP_TIME)

    routing.AddDimension(
        time_evaluator_index,
        0,  # Does not allow waiting time.
        trip_end_time,  # Global maximum time for a vehicle.
        False,  # Time will not start from 0.
        time_dimension_name,
    )
    time_dimension = routing.GetDimensionOrDie(time_dimension_name)
    # Vehicle started at start_time from depot, but will start at cur_time from re-navigated route.
    cur_time = int(cur_time)
    time_dimension.CumulVar(routing.Start(0)).SetRange(cur_time, cur_time)


def add_single_delivery_time_constraint(routing, manager, data, time_dimension_name):
    time_dimension = routing.GetDimensionOrDie(time_dimension_name)
    for location_idx, delivery_time in enumerate(data["delivery_time"]):
        if location_idx == data["end"][0]:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.SetCumulVarSoftUpperBound(
            index, int(delivery_time), LATE_DELIVERY_PENALTY_PER_SEC
        )


def extract_data(data, points_to_take, vehicles, start_time):
    updated_data = {
        "time_matrix": [
            [
                data["time_matrix"][point_src][point_dest]
                for point_dest in points_to_take
            ]
            for point_src in points_to_take
        ],
        "num_locations": len(points_to_take),
        "num_vehicles": len(vehicles),
        "depot": data["depot"],
        "vehicle_capacity": [data["capacity"][vehicle_id] for vehicle_id in vehicles],
        "start_time": start_time,
        "delivery_time": [data["delivery_time"][point] for point in points_to_take],
        "package_volume": [data["package_volume"][point] for point in points_to_take],
        "service_time": [data["service_time"][point] for point in points_to_take],
    }

    return updated_data
