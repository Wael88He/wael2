from rest_framework.views import APIView
from rest_framework.response import Response
from fcm_django.models import FCMDevice
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from rest_framework.generics import RetrieveAPIView
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from .models import *
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission

from rest_framework.permissions import AllowAny
from .serializers import UserSerializer

class UserRegistrationView(APIView):
    def post(self, request):
        user_serializer = UserSerializer(data=request.data,context={'request': request})
        
        userISerializer = UserISerializer(data=request.data,context={'request': request})
        if user_serializer.is_valid(raise_exception=True) and userISerializer.is_valid(raise_exception=True):
        
            user = user_serializer.save()
            profile = userISerializer.save(user=user)
        
           
            response_data = {
                "status": "success",
                "message": "User and profile created successfully",
                "user": user_serializer.data,
                "profile": userISerializer.data
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
    def get(self, request, *args, **kwargs):
        user_instance = User.objects.get(id=self.request.user.id)
        profile_instance = self.get_object()
        user_data = {
            'username': user_instance.username,
            'email': user_instance.email,
        }
        profile_data = UserISerializer(profile_instance).data
        data = {
            'user': user_data,
            'profile': profile_data,
        }
        return Response(data)
    def put(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Determine which fields were updated
        updated_fields = []
        for field in serializer.validated_data:
            
            if serializer.validated_data[field] != getattr(instance, field):
                updated_fields.append(field)

        # Return response with updated fields
        response_data = {'updated_fields': updated_fields}
        response_data.update(serializer.data)
        return Response(response_data)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user is not None:
            login(request, user)

            # Store the FCM registration token for the user
            registration_token = request.data.get('registration_token')
            if registration_token is not None:
                device = create_or_update_fcm_device(registration_token, user)

            refresh = RefreshToken.for_user(user)
            return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})
    return Response({'message':'username or password incorrect'}, status=status.HTTP_400_BAD_REQUEST)

def create_or_update_fcm_device(registration_token, user):
    # Delete any old FCMDevice objects with the same registration ID but a different user
    FCMDevice.objects.filter(registration_id=registration_token).exclude(user=user).delete()

    # Create or update the FCMDevice object for the user
    device, created = FCMDevice.objects.get_or_create(
        registration_id=registration_token,
        defaults={'type': 'android', 'user': user},
    )

    if not created:
        device.type = 'android'
        device.user = user
        device.save()

    return device
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
def logout_view(request):
    
    token = request.data.get('token')
    
    if not token:
        return Response({'message': 'Token not found in request body'}, status=status.HTTP_400_BAD_REQUEST)

    try:
       

        refresh_token = RefreshToken(token)
        
        refresh_token.blacklist()
        
        
        return Response({'message':'logout successfully'},status=status.HTTP_205_RESET_CONTENT)
    except:
        return Response({'message': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
from django.contrib.auth.models import User


from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from shapely.geometry import Point

@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
class DeleteAccountView(generics.GenericAPIView):

    def delete(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile
        user.delete()
        profile.delete()
        return Response({'message': 'Account Deleted'},status=status.HTTP_204_NO_CONTENT)
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    old_password = serializers.CharField(min_length=8)
    new_password = serializers.CharField(min_length=8)

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
class PasswordResetViewset(viewsets.ViewSet):
    serializer_class = PasswordResetSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(old_password):
            return Response({'message': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ForgetPasswordViewset(viewsets.ViewSet):
    serializer_class = ForgetPasswordSerializer

    @staticmethod
    def generate_code():
        return get_random_string(length=6, allowed_chars='0123456789')

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        code = self.generate_code()
        expiration_time = timezone.now() + timezone.timedelta(minutes=15)
        password_reset_code = PasswordResetCode.objects.create(user=user, code=code, expiration_time=expiration_time)
        password_reset_code.save()

        send_mail(
            'Password Reset Code',
            f'Your password reset code is {code}. This code will expire in 15 minutes.',
            'passwordreset@example.com',
            [email],
            fail_silently=False,
        )

        return Response({'message': 'Password reset code sent to your email'}, status=status.HTTP_200_OK)        



class PasswordResetConfirmationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8)

class PasswordResetConfirmationViewset(viewsets.ViewSet):
    serializer_class = PasswordResetConfirmationSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

        try:
            password_reset_code = PasswordResetCode.objects.get(user=user, code=code)
        except PasswordResetCode.DoesNotExist:
            return Response({'message': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

        if not password_reset_code.is_valid():
            return Response({'message': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        password_reset_code.delete()

        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)