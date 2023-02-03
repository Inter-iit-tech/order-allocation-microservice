from solver.serializers import (
    StartDaySerializer,
    AddPickupSerializer,
    DeletePickupSerializer,
)
from rest_framework import generics


class SolutionStartDay(generics.CreateAPIView):
    serializer_class = StartDaySerializer


class SolutionAddPickup(generics.CreateAPIView):
    serializer_class = AddPickupSerializer


class SolutionDeletePickup(generics.CreateAPIView):
    serializer_class = DeletePickupSerializer
