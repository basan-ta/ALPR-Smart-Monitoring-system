from django.contrib import admin
from .models import (
    Vehicle, Sighting, Alert, PredictedRoute,
    PoliceVehicleRegistration, StolenVehicleReport, OwnerWatchlist, VerificationAttempt,
    DatasetVersion,
)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "status", "owner", "last_seen", "created_at")
    search_fields = ("plate_number", "owner")
    list_filter = ("status",)


@admin.register(Sighting)
class SightingAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "vehicle", "latitude", "longitude", "speed_kmh", "heading_deg", "timestamp")
    search_fields = ("plate_number",)
    list_filter = ("timestamp",)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "status", "timestamp", "acknowledged", "dispatched")
    search_fields = ("plate_number",)
    list_filter = ("status", "acknowledged", "dispatched")


@admin.register(PredictedRoute)
class PredictedRouteAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "generated_at")
    search_fields = ("plate_number",)

# Register your models here.


@admin.register(PoliceVehicleRegistration)
class PoliceVehicleRegistrationAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "make", "model", "owner_name", "registered_at", "region_code")
    search_fields = ("plate_number", "owner_name")
    list_filter = ("region_code",)


@admin.register(DatasetVersion)
class DatasetVersionAdmin(admin.ModelAdmin):
    list_display = ("version_label", "applied_at", "records_vehicles", "records_sightings", "records_alerts")
    search_fields = ("version_label", "notes")
    list_filter = ("applied_at",)


@admin.register(StolenVehicleReport)
class StolenVehicleReportAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "case_number", "status", "report_timestamp")
    search_fields = ("plate_number", "case_number")
    list_filter = ("status",)


@admin.register(OwnerWatchlist)
class OwnerWatchlistAdmin(admin.ModelAdmin):
    list_display = ("owner_name", "reason", "active", "flagged_at")
    search_fields = ("owner_name",)
    list_filter = ("active",)


@admin.register(VerificationAttempt)
class VerificationAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "verification_timestamp", "match_status", "flag_category", "confidence", "response_time_ms")
    search_fields = ("id", "flag_category")
    list_filter = ("flag_category", "match_status")
