class Package:
    def __init__(self, volume):
        self.volume = volume


class Consignment:
    def __init__(self, consignmentType, point, expectedTime, package, serviceTime):
        self.consignment_type = consignmentType
        self.point = point
        self.expected_time = expectedTime
        self.package = Package(**package)
        self.service_time = serviceTime


class Vehicle:
    def __init__(self, capacity):
        self.capacity = capacity


class RiderMeta:
    def __init__(self, vehicle, startTime):
        self.vehicle = Vehicle(**vehicle)
        self.start_time = startTime
