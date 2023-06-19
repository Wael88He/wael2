from django.db import models

from shapely.geometry import Point
class Earthquake(models.Model):
    place = models.CharField(max_length=200, null=True)
    magnitude = models.FloatField()
    time = models.DateTimeField()
    depth = models.FloatField()
    latitude = models.FloatField()
    longitude = models.FloatField()

    @property
    def point_egeometry(self):
        return f'POINT({self.longitude} {self.latitude})'

    def __str__(self):
        return f'{self.magnitude} magnitude earthquake at {self.place} on {self.time}'
    