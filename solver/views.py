from solver.serializers import StartDaySerializer
from rest_framework import generics


class SolutionCreate(generics.CreateAPIView):
    serializer_class = StartDaySerializer
