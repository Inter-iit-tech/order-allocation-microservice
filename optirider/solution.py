from optirider.constants import (
    GLOBAL_START_TIME,
    WAIT_TIME_AT_WAREHOUSE,
    GLOBAL_END_TIME,
    TIME_DIMENSION_NAME,
)


def get_solution(data, manager, routing, solution, drop_penalty):

    num_vehicles = data["num_vehicles"]
    answer = [[] for _ in range(num_vehicles)]
    timings = [[] for _ in range(num_vehicles)]

    return_time = [
        GLOBAL_START_TIME
    ] * num_vehicles  # Time at which each vehicle will reach at wawrehouse after the trip.
    new_drop_penalty = [miss_penalty for miss_penalty in drop_penalty]

    time_dimension = routing.GetDimensionOrDie(TIME_DIMENSION_NAME)

    for vehicle_id in range(num_vehicles):

        index = routing.Start(vehicle_id)

        while not routing.IsEnd(index):
            curNode = manager.IndexToNode(index)
            curtime = solution.Value(time_dimension.CumulVar(index))
            new_drop_penalty[curNode] = 0

            answer[vehicle_id].append(curNode)
            timings[vehicle_id].append(curtime)
            index = solution.Value(routing.NextVar(index))

        curNode = manager.IndexToNode(index)
        curtime = solution.Value(time_dimension.CumulVar(index))
        new_drop_penalty[curNode] = 0

        answer[vehicle_id].append(curNode)
        timings[vehicle_id].append(curtime)

        return_time[vehicle_id] = curtime

    data["start_time"] = [
        min(val + WAIT_TIME_AT_WAREHOUSE, GLOBAL_END_TIME) for val in return_time
    ]

    return answer, timings, data, new_drop_penalty
