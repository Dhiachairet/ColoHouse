from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Campus, RoommateProfile, User


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ['id', 'name', 'university', 'address', 'latitude', 'longitude']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    campus = CampusSerializer(read_only=True)
    campus_id = serializers.PrimaryKeyRelatedField(
        queryset=Campus.objects.all(), source='campus', write_only=True, allow_null=True, required=False
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone', 'profile_picture', 'bio',
            'university', 'field_of_study', 'campus', 'campus_id',
            'push_enabled', 'notify_requests', 'notify_messages', 'date_joined',
        ]
        read_only_fields = ['id', 'email', 'date_joined']
        extra_kwargs = {
            'first_name': {'allow_blank': False},
            'last_name': {'allow_blank': False},
        }

    def validate_profile_picture(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('The picture must be smaller than 5 MB.')
        return value


class PreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoommateProfile
        fields = [
            'budget', 'preferred_room_type', 'move_in_date', 'max_distance_to_campus',
            'sleep_schedule', 'noise_tolerance', 'cleanliness', 'smoker', 'accepts_smokers',
            'looking_for_room', 'updated_at',
        ]
        read_only_fields = ['updated_at']
