from datetime import timedelta
import numpy as np
from optirider.services import fetch_distance_matrix
from optirider.setup import create_data_model
from optirider.start_day import start_day


class Point:
    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude
        self.coords = self.get_coords()

    def get_coords(self):
        return self.longitude, self.latitude


class Package:
    def __init__(self, volume):
        self.volume = volume


class Order:
    def __init__(self, id, orderType, point, expectedTime, package, serviceTime):
        self.id = id
        self.orderType = orderType
        self.point = Point(**point)
        self.expectedTime = expectedTime
        self.package = Package(**package)
        self.serviceTime = serviceTime


class Vehicle:
    def __init__(self, capacity):
        self.capacity = capacity


class Depot:
    def __init__(self, id, point):
        self.id = id
        self.point = Point(**point)


class RiderStartMeta:
    def __init__(self, vehicle, startTime):
        self.vehicle = Vehicle(**vehicle)
        self.startTime = startTime


class TourStop:
    def __init__(self, orderId, timing):
        self.orderId = orderId
        self.timing = timing


class StartDay:
    def __init__(self, riders, orders, depot):
        self.riders = [RiderStartMeta(**rider) for rider in riders]
        self.orders = [Order(**order) for order in orders]
        self.depot = Depot(**depot)
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
        points = [order.point for order in self.orders]
        points.insert(0, self.depot.point)
        return fetch_distance_matrix(points)

    def get_capacities(self):
        return [rider.vehicle.capacity for rider in self.riders]

    def get_start_times(self):
        return [int(np.rint(rider.startTime.total_seconds())) for rider in self.riders]

    def get_service_times(self):
        service_times = [
            int(np.rint(order.serviceTime.total_seconds())) for order in self.orders
        ]
        service_times.insert(0, 0)
        return service_times

    def get_package_volumes(self):
        package_volumes = [
            order.package.volume
            if order.orderType == "delivery"
            else -order.package.volume
            for order in self.orders
        ]
        package_volumes.insert(0, 0)
        return package_volumes

    def get_delivery_times(self):
        delivery_times = [
            int(np.rint(order.expectedTime.total_seconds())) for order in self.orders
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
                            self.depot.id
                            if tour_stop == 0
                            else self.orders[tour_stop - 1].id,
                            timedelta(
                                seconds=(
                                    timings[rider_index][tour_index][stop_index]
                                    - prev_time
                                )
                            ),
                        )
                    )
                    prev_time = timings[rider_index][tour_index][stop_index]
