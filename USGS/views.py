import requests
import time
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
import pytz
from django.utils import timezone
from django.contrib.auth.models import User
from Details.views import *
from Details.serializers import UserSerializer
from shapely.geometry import Point
from shapely.ops import transform
import pyproj
class EarthquakeView(APIView):
    def post(self, request):
        url = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
        data = request.data
        days = data.get('days', 1)  # Default to 1 day if not provided
        
        params = {
            'format': 'geojson',
            'starttime': '',
            'minmagnitude': '2.5'
        }
        headers = {
            'User-Agent': 'my-app/0.0.1'
        }
        
        start_time = datetime.utcnow() - timedelta(days=days)
        start_time_iso = start_time.isoformat() + 'Z'
        params['starttime']=start_time_iso
        #print(start_time_iso)
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            earthquakes = []
            for feature in data['features']:
                properties = feature['properties']
                place = properties['place']
                magnitude = properties['mag']
                time_unix = properties['time']
                time_str = datetime.fromtimestamp(time_unix / 1000)
                timezone = pytz.timezone('Asia/Damascus')
                time_aware = timezone.localize(time_str)
                longitude = feature['geometry']['coordinates'][0]
                latitude = feature['geometry']['coordinates'][1]
                depth = feature['geometry']['coordinates'][2]
                
                earthquake = {'place': place, 'magnitude': magnitude,
                'time': time_aware, 'depth': depth,'longitude':longitude,'latitude':latitude}
                #print(earthqua
                earthquakes.append(earthquake)
                
            return Response({'latest earthquakes': earthquakes})
        else:
            return Response({'error': 'Error retrieving earthquake data'})

def get_latest_earthquake_data():
    url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson'
    response = requests.get(url)
    data = response.json()
    earthquake = data['features'][0]
    return earthquake

from django.db.models import Q
from firebase_admin.messaging import Notification , MulticastMessage,Message
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes
from fcm_django.models import FCMDevice
from django.http import HttpResponse

class AffectedUsers(APIView):
    def get(self, request):
        #earthquake = get_latest_earthquake_data()
        earthquake={
  "type": "Feature",
  "properties": {
    "mag": 7.7,
    "place": "Southern Alaska",
    "time": 1625180223060
  },
  "geometry": {
    "type": "Point",
    "coordinates": [
      33.515635808708694, 36.27114325003677,
      34.6
    ]
  }
}
        affected_users = Profile.objects.filter(Q(latitude__isnull=False) & Q(longitude__isnull=False)
    )

        project_meters = pyproj.Transformer.from_crs('epsg:4326', 'epsg:3857', always_xy=True).transform
        # Convert the earthquake coordinates to a Shapely Point object and to meters
        earthquake_point = Point(earthquake['geometry']['coordinates'])
        print('epoint : ',earthquake_point)
        earthquake_point_meters = transform(project_meters, earthquake_point)
        #print('epointm :',earthquake_point_meters)

        
        radius_meters = ((earthquake['properties']['mag'] * 110) / 2) * 1000
        print('R:',radius_meters)

        affected_users_tokens=[]
        for user in affected_users:
        # Convert the user coordinates to a Shapely Point object and to meters
         user_point = Point(user.longitude, user.latitude)
         
         user_point_meters = transform(project_meters, user_point)

         distance_meters = earthquake_point_meters.distance(user_point_meters)
         #print('dis:',distance_meters)
         

         if distance_meters <= radius_meters:
            print('affected : ',user.user,user_point)
            fcm_device = FCMDevice.objects.filter(user=user.user).first()
            if fcm_device:
                affected_users_tokens.append(fcm_device)
        message=Message(
        notification=Notification(
            title=f'New earthquake in {place}!',
            body=f'A {mag} magnitude earthquake occurred at {time}',
            image='https://npr.brightspotcdn.com/dims4/default/7bca66e/2147483647/strip/true/crop/1760x1085+0+0/resize/880x543!/quality/90/?url=http%3A%2F%2Fnpr-brightspot.s3.amazonaws.com%2F08%2F65%2F79d6935f4122845e17f6bb0ebf0e%2Fearthquake-vector-symbol.png'
        )) 
        for device in affected_users_tokens:
         device.send_message(message)
         print(device)
        return HttpResponse({'message :Notifications sent.'})




@api_view(('POST',))
@csrf_exempt
def send_notification(request):
 
    # Create a notification message
    message=Message(
        notification=Notification(
            title=f'New earthquake in Tarama,Japan!',
            body=f'A 5.2 magnitude earthquake occurred at July 10, 2022, 3:30 PM',
            image='https://npr.brightspotcdn.com/dims4/default/7bca66e/2147483647/strip/true/crop/1760x1085+0+0/resize/880x543!/quality/90/?url=http%3A%2F%2Fnpr-brightspot.s3.amazonaws.com%2F08%2F65%2F79d6935f4122845e17f6bb0ebf0e%2Fearthquake-vector-symbol.png'
        ),
        
    )
    
    devices = FCMDevice.objects.all()
    #print(devices)
    response= devices.send_message(message)
    return HttpResponse(f'{response} messages were sent successfully!')