from rest_framework import serializers
from .models import Vehicle, Sighting, Alert, PredictedRoute
from .services.nepali_plates import convert_plate_to_nepali
from .models import (
    PoliceVehicleRegistration,
    StolenVehicleReport,
    OwnerWatchlist,
    VerificationAttempt,
)


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            'id', 'plate_number', 'status', 'owner', 'last_seen', 'notes',
            'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['plate_number'] = convert_plate_to_nepali(data.get('plate_number'))
        except Exception:
            # Preserve original on failure
            pass
        return data


class SightingSerializer(serializers.ModelSerializer):
    # Include nested vehicle details to support frontend map status and display
    vehicle = VehicleSerializer(read_only=True)

    class Meta:
        model = Sighting
        fields = [
            'id', 'plate_number', 'vehicle', 'vehicle_type', 'color',
            'latitude', 'longitude', 'speed_kmh', 'heading_deg', 'timestamp'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['plate_number'] = convert_plate_to_nepali(data.get('plate_number'))
        except Exception:
            pass
        return data


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            'id', 'plate_number', 'vehicle', 'status', 'timestamp',
            'predicted_latitude', 'predicted_longitude', 'message',
            'acknowledged', 'dispatched', 'created_at'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['plate_number'] = convert_plate_to_nepali(data.get('plate_number'))
        except Exception:
            pass
        return data


class PredictedRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictedRoute
        fields = ['id', 'plate_number', 'path', 'generated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['plate_number'] = convert_plate_to_nepali(data.get('plate_number'))
        except Exception:
            pass
        return data


class VerificationRequestSerializer(serializers.Serializer):
    plate_number = serializers.CharField(max_length=64)
    make = serializers.CharField(max_length=64, required=False, allow_blank=True)
    model = serializers.CharField(max_length=64, required=False, allow_blank=True)
    owner_name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    region_code = serializers.CharField(max_length=32, required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(required=False)


class VerificationResponseSerializer(serializers.Serializer):
    match_status = serializers.BooleanField()
    flag_category = serializers.ChoiceField(choices=['stolen', 'suspicious', 'normal'])
    confidence = serializers.FloatField()
    verification_timestamp = serializers.CharField()
    reference_case_numbers = serializers.ListField(child=serializers.CharField())
    response_time_ms = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)