from django.http import JsonResponse
from django.contrib.auth import get_user_model
from Details.models import Profile
from .models import Health
import joblib
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, authentication_classes,permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
import json
import numpy as np
from django.views.decorators.csrf import csrf_exempt

@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
@api_view(['GET', 'POST', 'PUT'])
def predict_risk_level(request):
    user = request.user
    profile = Profile.objects.get(user=user)
    try:
        health = Health.objects.get(user=user)
        data = {
            'systolic_bp': health.systolic_bp,
            'diastolic_bp': health.diastolic_bp,
            'heart_rate': health.heart_rate,
            'risk_level': health.risk_level,
        }
        if request.method == 'GET':
            return JsonResponse(data)
    except Health.DoesNotExist:
        health = None

    if request.method == 'POST' or request.method == 'PUT':
        # Retrieve the input data from the request body
        data = json.loads(request.body)
        systolic_bp = data.get('systolic_bp')
        diastolic_bp = data.get('diastolic_bp')
        heart_rate = data.get('heart_rate')

        # Load the trained model and label encoder from the joblib files
        model = joblib.load('health.py')
        label_encoder = joblib.load('label_encoder.joblib')

        # Make a prediction
        new_data = [[profile.age, systolic_bp, diastolic_bp, heart_rate]]
        predicted = model.predict(new_data)
        predicted_decoded = label_encoder.inverse_transform(np.argmax(predicted, axis=1))

        if request.method == 'POST':
            # Create a new Health object with the input data and predicted risk level
            if health is None:
                health = Health(user=user, systolic_bp=systolic_bp, diastolic_bp=diastolic_bp, heart_rate=heart_rate, risk_level=predicted_decoded[0])
                health.save()
            else:
                return JsonResponse({'message': 'Health object already exists for this user.'}, status=400)
        elif request.method == 'PUT':
            # Update the existing Health object with the input data and predicted risk level
            if health is not None:
                health.systolic_bp = systolic_bp
                health.diastolic_bp = diastolic_bp
                health.heart_rate = heart_rate
                health.risk_level = predicted_decoded[0]
                health.save()
            else:
                return JsonResponse({'message': 'No Health object found for this user.'}, status=404)

        # Return the predicted risk level as a JSON response
        return JsonResponse({'message': predicted_decoded[0]})
    else:
        # Return an error response if the request method is not supported
        return JsonResponse({'message': 'Unsupported request method.'}, status=405)


import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
API_URL = "https://api-inference.huggingface.co/models/alaa1997/ArabicSpeechToTextModel"
headers = {"Authorization": "Bearer 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"}

@api_view(['POST'])
def audio_to_text(request):
    if request.method == 'POST':
        audio_file = request.FILES.get('audio')
        
        if audio_file is None:
            return Response({'message': 'No audio file was uploaded.'}, status=400)
        if not hasattr(audio_file, 'read'):
            return Response({'message': 'Invalid audio file format.'}, status=400)
    

        # Make a request to the Hugging Face API to convert the audio to text
        response = requests.post(API_URL, headers=headers, data=audio_file.read())
        response_data = response.json()
        
        # Extract the text from the response data
        text = response_data['text']
        utf8_text = text.encode('utf-8')
        # Return the text as a JSON response
        return Response({'text': utf8_text})
    else:
        # Return an error response if the request method is not supported
        return Response({'message': 'Unsupported request method.'}, status=405)