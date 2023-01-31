import numpy as np
from optisolver.services import fetch_distance_matrix


class Package:
    def __init__(self, volume):
        self.volume = volume


class Consignment:
    def __init__(self, consignmentType, point, expectedTime, package, serviceTime):
        self.consignmentType = consignmentType
        self.point = point
        self.expectedTime = expectedTime
        self.package = Package(**package)
        self.serviceTime = serviceTime


class Vehicle:
    def __init__(self, capacity):
        self.capacity = capacity


class RiderMeta:
    def __init__(self, vehicle, startTime):
        self.vehicle = Vehicle(**vehicle)
        self.startTime = startTime


class StartDay:
    def __init__(self, riders, consignments, depotPoint):
        self.riders = [RiderMeta(**rider) for rider in riders]
        self.consignments = [Consignment(**consignment) for consignment in consignments]
        self.depotPoint = depotPoint
        self.tours = None
        self.timings = None
        self._start_day()

    def _start_day(self):
        duration_matrix = self.get_distance_matrix()
        capacities = [rider.vehicle.capacity for rider in self.riders]
        start_times = [
            int(np.rint(rider.startTime.timestamp())) for rider in self.riders
        ]
        service_times = [
            int(np.rint(consignment.serviceTime.total_seconds()))
            for consignment in self.consignments
        ]
        service_times.insert(0, 0)
        package_volumes = [
            consignment.package.volume for consignment in self.consignments
        ]
        package_volumes.insert(0, 0)
        delivery_times = [
            int(np.rint(consignment.expectedTime.timestamp()))
            for consignment in self.consignments
        ]
        delivery_times.insert(0, 0)
        penalty = [int(np.sum(duration_matrix))] * len(duration_matrix)
        print(
            duration_matrix,
            capacities,
            start_times,
            service_times,
            package_volumes,
            delivery_times,
            penalty,
        )

    def get_distance_matrix(self):
        points = [consignment.point for consignment in self.consignments]
        points.insert(0, self.depotPoint)
        return fetch_distance_matrix(points)
