#from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models


    # other fields and methods
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(blank=True, null=True,max_length=255)
    age = models.IntegerField(blank=True, null=True)
    image = models.ImageField(upload_to='user_images/', blank=True, null=True)
    address = models.CharField(blank=True, null=True,max_length=255)
    illnesses = models.TextField(blank=True, null=True)
    family_members=models.IntegerField(default=1,blank=True)
    phone = models.CharField(blank=True, null=True,max_length=20)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.email} Profile'




class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expiration_time = models.DateTimeField()
    def is_valid(self):
        """
        Checks whether the code is valid and not expired.
        """
        now = timezone.now()
        return self.expiration_time > now
    def __str__(self):
        return f'{self.user.email} - {self.code}'        