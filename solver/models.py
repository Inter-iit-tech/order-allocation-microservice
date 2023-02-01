from datetime import timedelta
import numpy as np
from optirider.services import fetch_distance_matrix
from optirider.setup import create_data_model
from optirider.start_day import start_day


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


class TourStop:
    def __init__(self, locationIndex, timing):
        self.locationIndex = locationIndex
        self.timing = timing


class StartDay:
    def __init__(self, riders, consignments, depotPoint):
        self.riders = [RiderMeta(**rider) for rider in riders]
        self.consignments = [Consignment(**consignment) for consignment in consignments]
        self.depotPoint = depotPoint
        self.tours = None
        self._start_day()

    def _start_day(self):
        duration_matrix = self.get_distance_matrix()
        capacities = self.get_capacities()
        start_times = self.get_start_times()
        service_times = self.get_service_times()
        package_volumes = self.get_package_volumes()
        delivery_times = self.get_delivery_times()

        data = create_data_model(
            duration_matrix,
            capacities,
            start_times,
            service_times,
            package_volumes,
            delivery_times,
            num_vehicles=len(self.riders),
            depot=0,
        )

        penalty = [int(np.sum(duration_matrix))] * len(duration_matrix)
        tours, timings, total_penalty = start_day(data, penalty)
        self.zip_tours_and_timings(tours, timings)

    def get_distance_matrix(self):
        points = [consignment.point for consignment in self.consignments]
        points.insert(0, self.depotPoint)
        return fetch_distance_matrix(points)

    def get_capacities(self):
        return [rider.vehicle.capacity for rider in self.riders]

    def get_start_times(self):
        return [int(np.rint(rider.startTime.total_seconds())) for rider in self.riders]

    def get_service_times(self):
        service_times = [
            int(np.rint(consignment.serviceTime.total_seconds()))
            for consignment in self.consignments
        ]
        service_times.insert(0, 0)
        return service_times

    def get_package_volumes(self):
        package_volumes = [
            consignment.package.volume
            if consignment.consignmentType == "delivery"
            else -consignment.package.volume
            for consignment in self.consignments
        ]
        package_volumes.insert(0, 0)
        return package_volumes

    def get_delivery_times(self):
        delivery_times = [
            int(np.rint(consignment.expectedTime.total_seconds()))
            for consignment in self.consignments
        ]
        delivery_times.insert(0, 0)
        return delivery_times

    def zip_tours_and_timings(self, tours, timings):
        self.tours = []
        for rider_index, rider_tours in enumerate(tours):
            self.tours.append([])
            for tour_index, tour in enumerate(rider_tours):
                self.tours[rider_index].append([])
                prev_time = 0
                for stop_index, tour_stop in enumerate(tour):
                    self.tours[rider_index][tour_index].append(
                        TourStop(
                            tour_stop,
                            timedelta(
                                seconds=(
                                    timings[rider_index][tour_index][stop_index]
                                    - prev_time
                                )
                            ),
                        )
                    )
                    prev_time = timings[rider_index][tour_index][stop_index]
