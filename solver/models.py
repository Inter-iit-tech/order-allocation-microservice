class Package:
    def __init__(self, volume):
        self.volume = volume


class Consignment:
    def __init__(self, consignmentType, point, expectedTime, package):
        self.consignment_type = consignmentType
        self.point = point
        self.expected_time = expectedTime
        self.package = Package(**package)
