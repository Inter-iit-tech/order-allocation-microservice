from optirider.constants import WAIT_TIME_AT_WAREHOUSE, GLOBAL_START_TIME


def get_solution(data, manager, routing, solution, drop_penalty):
    """Prints solution on console.

    :param data: Data, as arranged by :ref:`create_data_model`
    :param ortools.constraint_solver.pywrapcp.RoutingIndexManager manager: Node manager
    :param ortools.constraint_solver.pywrapcp.RoutingModel routing: OR Tools routing model
    """
    # print(f"Objective: {solution.ObjectiveValue()}")

    num_vehicles = data["num_vehicles"]
    answer = [[] for _id in range(num_vehicles)]
    timings = [[] for id in range(num_vehicles)]
    return_time = [GLOBAL_START_TIME] * num_vehicles
    new_drop_penalty = [0] * data["num_locations"]

    late_delivery_penalty = 0
    missing_delivery_penalty = 0
    time_taken = 0

    space_dimension = routing.GetDimensionOrDie("Free Space")
    time_dimension = routing.GetDimensionOrDie("Time")

    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        # print("Route for vehicle {}:".format(vehicle_id))
        start_time = solution.Value(time_dimension.CumulVar(index))
        while not routing.IsEnd(index):
            curNode = manager.IndexToNode(index)
            curfreespace = space_dimension.CumulVar(index)
            curtime = time_dimension.CumulVar(index)
            late_delivery_penalty += (
                max(0, solution.Value(curtime) - data["delivery_time"][curNode]) * 10
            )
            # print(curNode, solution.Value(curfreespace),
            #       data["delivery_time"][curNode])
            answer[vehicle_id].append(curNode)
            timings[vehicle_id].append(solution.Value(curtime))
            index = solution.Value(routing.NextVar(index))
        curNode = manager.IndexToNode(index)
        curfreespace = space_dimension.CumulVar(index)
        curtime = time_dimension.CumulVar(index)
        timings[vehicle_id].append(solution.Value(curtime))
        # print(curNode, solution.Value(curfreespace),
        #       data["delivery_time"][curNode])
        return_time[vehicle_id] = solution.Value(curtime)
        time_taken += return_time[vehicle_id] - start_time
        answer[vehicle_id].append(curNode)

    data["start_time"] = [val + WAIT_TIME_AT_WAREHOUSE for val in return_time]
    # dropped_nodes = "Dropped nodes:"
    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if solution.Value(routing.NextVar(node)) == node:
            new_drop_penalty[manager.IndexToNode(node)] = drop_penalty[
                manager.IndexToNode(node)
            ]
            missing_delivery_penalty += drop_penalty[manager.IndexToNode(node)]
    #         dropped_nodes += " {}".format(manager.IndexToNode(node))
    # print(late_delivery_penalty, missing_delivery_penalty, time_taken)

    return answer, timings, data, new_drop_penalty
