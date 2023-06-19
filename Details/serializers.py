from rest_framework import serializers

from django.contrib.auth.models import User 
from django.core.validators import MinLengthValidator,RegexValidator
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueValidator

from django.contrib.auth import get_user_model
from .models import User, Profile
User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[MinLengthValidator(8)]
    )
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserISerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    phone = serializers.CharField(required=False,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{9,15}$',
                message="Phone number must be in the format: '+999999999'. Up to 15 digits allowed.")])
    class Meta:
        model = Profile
        fields = '__all__'
    def create(self, validated_data):
        image = validated_data.pop('image', None)
        user_info = super().create(validated_data)
        if image:
            user_info.image = image
            user_info.save()
        return user_info
class ProfileUpdateSerializer(UserISerializer):
    class Meta(UserISerializer.Meta):
        read_only_fields = ['user']
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

