import requests
import time
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Earthquake
import pytz
from django.utils import timezone
from django.contrib.auth.models import User

#from django.contrib.gis.db.models.functions import Distance
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


from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.templatetags.static import static

class AffectedUsers(APIView):
    def get(self, request):
        # Get the longitude and latitude from the query parameters
        affected_users = User.objects.filter(profile__longitude=longitude, profile__latitude=latitude)

        # Define a projection that converts lat/long coordinates to meters
        project_meters = pyproj.Transformer.from_crs('epsg:4326', 'epsg:3857', always_xy=True).transform

        # Convert the user coordinates to a Shapely Point object and to meters
        user_point = Point(longitude, latitude)
        user_point_meters = transform(project_meters, user_point)

        # Calculate the radius based on the user's proximity to the affected locations
        max_distance_km = 100  # maximum distance to consider in km
        radius_meters = max_distance_km * 1000

        # Filter out locations whose distance from the user is greater than the radius
        affected_locations = []
        for location in Location.objects.all():
            # Convert the location point to meters
            location_point = location.point_geometry
            location_point_meters = transform(project_meters, location_point)

            # Calculate the distance between the user and location in meters
            distance_meters = user_point_meters.distance(location_point_meters)

            # If the distance is less than or equal to the radius, add the location to the affected locations list
            if distance_meters <= radius_meters:
                affected_locations.append(location)

        # Retrieve the email addresses of the affected users
        affected_users = User.objects.filter(location__in=affected_locations).distinct()

        # Create a message body that includes the earthquake information and the image
        message_body = render_to_string('email_template.html', {'locations': affected_locations})
        message_body_text = strip_tags(message_body)

        # Add the image to the email as an attachment
        png_path = 'earthquake-vector-symbol.png'
        with open(png_path, 'rb') as f:
            png_data = f.read()
        png_filename = 'earthquake.png'
        png_mime_type = 'image/png'

        # Create an EmailMultiAlternatives object and attach the PNG image
        email = EmailMultiAlternatives(
            'Location Alert',
            message_body_text,
            settings.DEFAULT_FROM_EMAIL,
            [user.email for user in affected_users],
        )
        email.attach(png_filename, png_data, png_mime_type)

        # Send the email to the affected users
        email.send()

        # Serialize the affected locations and return the response
        serializer = LocationSerializer(affected_locations, many=True)
        return Response(serializer.data)

def get_latest_earthquake_data():
    url = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson'
    response = requests.get(url)
    data = response.json()
    return data
from fcm_django.models import FCMDevice

def get_users_registration_tokens():
    users = User.objects.all()
    registration_tokens = FCMDevice.objects.filter(user__in=users).values_list('registration_id', flat=True)
    return list(registration_tokens)

from firebase_admin.messaging import Notification , MulticastMessage,Message
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes
from fcm_django.models import FCMDevice
from django.http import HttpResponse
@api_view(('POST',))
@csrf_exempt
def send_notification(request):
    
    #earthquake_data = get_latest_earthquake_data()

    
    #location = earthquake_data['features'][0]['properties']['place']
    #magnitude = earthquake_data['features'][0]['properties']['mag']
    #time = earthquake_data['features'][0]['properties']['time']

    # Get the registration tokens for all users in the database
    registration_tokens = get_users_registration_tokens()

    # Create a notification message
    message=Message(
        notification=Notification(
            title=f'New earthquake in Tarama,Japan!',
            body=f'A 5.2 magnitude earthquake occurred at July 10, 2022, 3:30 PM',
            image='https://npr.brightspotcdn.com/dims4/default/7bca66e/2147483647/strip/true/crop/1760x1085+0+0/resize/880x543!/quality/90/?url=http%3A%2F%2Fnpr-brightspot.s3.amazonaws.com%2F08%2F65%2F79d6935f4122845e17f6bb0ebf0e%2Fearthquake-vector-symbol.png'
        ),
        #tokens=registration_tokens,
    )
    #for device in devices ...
    devices = FCMDevice.objects.all()
    response= devices.send_message(message)

    # Return a response to the client
    return HttpResponse(f'{response} messages were sent successfully!')