from django.db import models
from django.utils import timezone
from django.db import models


class Vehicle(models.Model):
    STATUS_NORMAL = 'normal'
    STATUS_SUSPICIOUS = 'suspicious'
    STATUS_STOLEN = 'stolen'
    STATUS_CHOICES = [
        (STATUS_NORMAL, 'Normal'),
        (STATUS_SUSPICIOUS, 'Suspicious'),
        (STATUS_STOLEN, 'Stolen'),
    ]

    plate_number = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_NORMAL)
    owner = models.CharField(max_length=128, blank=True, default='')
    last_seen = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plate_number} ({self.status})"


class Sighting(models.Model):
    plate_number = models.CharField(max_length=32)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL, related_name='sightings')
    vehicle_type = models.CharField(max_length=64, blank=True, default='')
    color = models.CharField(max_length=64, blank=True, default='')
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed_kmh = models.FloatField(default=0)
    heading_deg = models.FloatField(default=0)  # 0-360 degrees, 0 is North
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.plate_number} @ {self.latitude:.5f},{self.longitude:.5f}"


class DatasetVersion(models.Model):
    """Track dataset migrations/versions applied to the system."""
    version_label = models.CharField(max_length=64, unique=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')
    records_vehicles = models.IntegerField(default=0)
    records_sightings = models.IntegerField(default=0)
    records_alerts = models.IntegerField(default=0)

    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['version_label']),
            models.Index(fields=['applied_at']),
        ]

    def __str__(self):
        return f"Dataset {self.version_label} @ {self.applied_at.isoformat()}"


class Alert(models.Model):
    plate_number = models.CharField(max_length=32)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL, related_name='alerts')
    status = models.CharField(max_length=16, choices=Vehicle.STATUS_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    predicted_latitude = models.FloatField(null=True, blank=True)
    predicted_longitude = models.FloatField(null=True, blank=True)
    message = models.CharField(max_length=256, blank=True, default='')
    acknowledged = models.BooleanField(default=False)
    dispatched = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ALERT {self.plate_number} [{self.status}]"


class PredictedRoute(models.Model):
    plate_number = models.CharField(max_length=32)
    path = models.JSONField(default=list)  # list of {lat, lon, t}
    generated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Route {self.plate_number} ({len(self.path)} pts)"

class PoliceVehicleRegistration(models.Model):
    """Authoritative police registration record for vehicles."""
    registration_id = models.CharField(max_length=64, unique=True)
    plate_number = models.CharField(max_length=32)
    make = models.CharField(max_length=64, blank=True, default='')
    model = models.CharField(max_length=64, blank=True, default='')
    owner_name = models.CharField(max_length=128, blank=True, default='')
    region_code = models.CharField(max_length=32, blank=True, default='')
    registered_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["plate_number"]),
            models.Index(fields=["owner_name"]),
        ]

    def __str__(self):
        return f"{self.plate_number} ({self.registration_id})"


class StolenVehicleReport(models.Model):
    """Police reports for stolen vehicles."""
    STATUS_OPEN = 'open'
    STATUS_RESOLVED = 'resolved'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_RESOLVED, 'Resolved'),
    ]

    case_number = models.CharField(max_length=64, unique=True)
    plate_number = models.CharField(max_length=32)
    registration = models.ForeignKey(PoliceVehicleRegistration, null=True, blank=True, on_delete=models.SET_NULL, related_name='stolen_reports')
    report_timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN)
    region_code = models.CharField(max_length=32, blank=True, default='')
    details = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["plate_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Case {self.case_number} - {self.plate_number} ({self.status})"


class OwnerWatchlist(models.Model):
    """Watchlist of owners flagged as suspicious."""
    owner_name = models.CharField(max_length=128)
    reason = models.CharField(max_length=256, blank=True, default='')
    flagged_at = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner_name"]),
            models.Index(fields=["active"]),
        ]

    def __str__(self):
        return f"{self.owner_name} (active={self.active})"


class VerificationAttempt(models.Model):
    """Audit log for vehicle verification requests and results."""
    input_payload = models.JSONField(default=dict)
    matched_registration = models.ForeignKey(PoliceVehicleRegistration, null=True, blank=True, on_delete=models.SET_NULL, related_name='verification_attempts')
    matched_stolen_report = models.ForeignKey(StolenVehicleReport, null=True, blank=True, on_delete=models.SET_NULL, related_name='verification_attempts')
    matched_owner_watchlist = models.ForeignKey(OwnerWatchlist, null=True, blank=True, on_delete=models.SET_NULL, related_name='verification_attempts')
    match_status = models.BooleanField(default=False)
    flag_category = models.CharField(max_length=16, default='normal')  # stolen/suspicious/normal
    confidence = models.FloatField(default=0.0)
    verification_timestamp = models.DateTimeField(default=timezone.now)
    response_time_ms = models.IntegerField(default=0)
    reference_case_numbers = models.JSONField(default=list)
    message = models.CharField(max_length=256, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Verify {self.input_payload.get('plate_number', '')} -> {self.flag_category} ({self.confidence:.0f}%)"
