from datetime import timedelta
import numpy as np
from optirider.services import fetch_distance_matrix
from optirider.setup import create_data_model, create_updated_data
from optirider.start_day import start_day
from optirider.add_pickup import add_pickup
from optirider.delete_pickup import delete_pickup


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
    def __init__(self, id, vehicle, startTime):
        self.id = id
        self.vehicle = Vehicle(**vehicle)
        self.startTime = startTime
        self.tours = []


class RiderUpdateMeta:
    def __init__(self, id, vehicle, tours, headingTo):
        self.id = id
        self.vehicle = Vehicle(**vehicle)
        self.tours = [[TourStop(**stop) for stop in tour] for tour in tours]
        self.headingTo = headingTo
        self.updatedCurrentTour = False


class TourStop:
    def __init__(self, orderId, timing):
        self.orderId = orderId
        self.timing = timing


class StartDayMeta:
    def __init__(self, riders, orders, depot):
        self.riders = [RiderStartMeta(**rider) for rider in riders]
        self.orders = [Order(**order) for order in orders]
        self.depot = Depot(**depot)
        self._start_day()

    def _start_day(self):
        depot_index = 0
        duration_matrix = get_distance_matrix(self.depot, self.orders)
        capacities = get_capacities(self.riders)
        start_times = get_start_times(self.riders)
        service_times = get_service_times(self.orders)
        package_volumes = get_package_volumes(self.orders)
        delivery_times = get_delivery_times(self.orders)

        data = create_data_model(
            duration_matrix,
            capacities,
            start_times,
            service_times,
            package_volumes,
            delivery_times,
            num_vehicles=len(self.riders),
            depot=depot_index,
        )

        penalty = [int(np.sum(duration_matrix))] * len(duration_matrix)
        tours, timings, total_penalty = start_day(data, penalty)
        zipped_tours = zip_tours_and_timings(tours, timings, self.depot, self.orders)
        for rider_index, tours_info in enumerate(zipped_tours):
            self.riders[rider_index].tours = tours_info


class AddPickupMeta:
    def __init__(self, riders, orders, depot, newOrder):
        self.riders = [RiderUpdateMeta(**rider) for rider in riders]
        self.orders = [Order(**order) for order in orders]
        self.orders.append(Order(**newOrder))
        self.depot = Depot(**depot)
        self._add_pickup()

    def _add_pickup(self):
        depot_index = 0
        pickup_index = len(self.orders)
        duration_matrix = get_distance_matrix(self.depot, self.orders)
        capacities = get_capacities(self.riders)
        service_times = get_service_times(self.orders)
        package_volumes = get_package_volumes(self.orders)
        delivery_times = get_delivery_times(self.orders)
        tours, timings, tour_locations = unzip_tours_timings_locations(
            self.riders, self.depot, self.orders
        )

        data = create_updated_data(
            duration_matrix,
            tour_locations,
            depot_index,
            pickup_index,
            service_times,
            package_volumes,
            delivery_times,
            capacities,
        )

        updated_tours, updated_timings, changed_rider = add_pickup(tours, timings, data)
        if 0 <= changed_rider < len(self.riders):
            self.riders[changed_rider].updatedCurrentTour = True

        zipped_tours = zip_tours_and_timings(
            updated_tours, updated_timings, self.depot, self.orders
        )
        for rider_index, tours_info in enumerate(zipped_tours):
            self.riders[rider_index].tours = tours_info


class DeletePickupMeta:
    def __init__(self, riders, orders, depot, delOrderId):
        self.riders = [RiderUpdateMeta(**rider) for rider in riders]
        self.orders = [Order(**order) for order in orders]
        self.depot = Depot(**depot)
        self.delOrderId = delOrderId
        self._del_pickup()

    def _del_pickup(self):
        depot_index = 0
        pickup_index = -1
        for order_index, order in enumerate(self.orders):
            if order.id == self.delOrderId:
                pickup_index = order_index + 1
                break
        if pickup_index == -1:
            return

        duration_matrix = get_distance_matrix(self.depot, self.orders)
        capacities = get_capacities(self.riders)
        service_times = get_service_times(self.orders)
        package_volumes = get_package_volumes(self.orders)
        delivery_times = get_delivery_times(self.orders)
        tours, timings, tour_locations = unzip_tours_timings_locations(
            self.riders, self.depot, self.orders
        )

        data = create_updated_data(
            duration_matrix,
            tour_locations,
            depot_index,
            pickup_index,
            service_times,
            package_volumes,
            delivery_times,
            capacities,
        )

        updated_tours, updated_timings, changed_rider = delete_pickup(
            tours, timings, data
        )
        if 0 <= changed_rider < len(self.riders):
            self.riders[changed_rider].updatedCurrentTour = True

        zipped_tours = zip_tours_and_timings(
            updated_tours, updated_timings, self.depot, self.orders
        )
        for rider_index, tours_info in enumerate(zipped_tours):
            self.riders[rider_index].tours = tours_info


def get_distance_matrix(depot, orders):
    points = [order.point for order in orders]
    points.insert(0, depot.point)
    return fetch_distance_matrix(points)


def get_capacities(riders):
    return [rider.vehicle.capacity for rider in riders]


def get_start_times(riders):
    return [int(np.rint(rider.startTime.total_seconds())) for rider in riders]


def get_service_times(orders):
    service_times = [
        int(np.rint(order.serviceTime.total_seconds())) for order in orders
    ]
    service_times.insert(0, 0)
    return service_times


def get_package_volumes(orders):
    package_volumes = [
        order.package.volume if order.orderType == "delivery" else -order.package.volume
        for order in orders
    ]
    package_volumes.insert(0, 0)
    return package_volumes


def get_delivery_times(orders):
    delivery_times = [
        int(np.rint(order.expectedTime.total_seconds())) for order in orders
    ]
    delivery_times.insert(0, 0)
    return delivery_times


def zip_tours_and_timings(tours, timings, depot, orders):
    zipped_tours = []
    for rider_index, rider_tours in enumerate(tours):
        zipped_tours.append([])
        if len(rider_tours) == 1 and len(rider_tours[0]) == 0:
            continue
        for tour_index, tour in enumerate(rider_tours):
            zipped_tours[rider_index].append([])
            prev_time = 0
            for stop_index, tour_stop in enumerate(tour):
                zipped_tours[rider_index][tour_index].append(
                    TourStop(
                        depot.id if tour_stop == 0 else orders[tour_stop - 1].id,
                        timedelta(
                            seconds=(
                                timings[rider_index][tour_index][stop_index] - prev_time
                            )
                        ),
                    )
                )
                prev_time = timings[rider_index][tour_index][stop_index]
    return zipped_tours


def unzip_tours_timings_locations(riders, depot, orders):
    id_to_index = {
        depot.id: 0,
    }
    for i, order in enumerate(orders):
        id_to_index[order.id] = i + 1
    tours = []
    timings = []
    tour_locations = []

    for rider in riders:
        tours.append([])
        timings.append([])
        tour_locations.append(0)

        if len(rider.tours) == 0:
            tours[-1].append([])
            timings[-1].append([])
            tour_locations[-1] = -1
            continue

        if rider.headingTo is not None:
            for stop_index in range(1, len(rider.tours[0])):
                stop = rider.tours[0][stop_index]
                if stop.orderId == rider.headingTo:
                    tour_locations[-1] = stop_index
                    break

        for tour in rider.tours:
            tours[-1].append([])
            timings[-1].append([])
            stop_time = 0
            for stop in tour:
                stop_time += int(stop.timing.total_seconds())
                tours[-1][-1].append(id_to_index[stop.orderId])
                timings[-1][-1].append(stop_time)

    return tours, timings, tour_locations
