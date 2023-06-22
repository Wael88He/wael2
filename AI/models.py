from django.db import models
from django.contrib.auth.models import User
from Details.models import Profile
class Health(models.Model):
 user = models.OneToOneField(User, on_delete=models.CASCADE)
 
 systolic_bp = models.IntegerField()
 diastolic_bp = models.IntegerField()
 heart_rate = models.IntegerField()
 risk_level= models.CharField(max_length=30)
