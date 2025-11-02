from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Sighting, Vehicle, Alert, PredictedRoute
from .services.prediction import predict_route
from .services.nepali_plates import normalize_plate as nepali_normalize


def normalize_plate_preserve_spacing(plate: str) -> str:
    """Normalize dash variants while preserving spacing for exact plate matching.

    Historically this function removed spaces which broke Vehicle lookups
    using __iexact. We now preserve spaces to ensure DB matches succeed.
    """
    p = (plate or '').strip()
    # Preserve spaces; only normalize uncommon dash variants
    return nepali_normalize(p)


@receiver(post_save, sender=Sighting)
def handle_new_sighting(sender, instance: Sighting, created: bool, **kwargs):
    if not created:
        return

    # Keep spacing for DB lookups and normalize only dashes
    plate = normalize_plate_preserve_spacing(instance.plate_number)

    # Prefer already-linked vehicle from the instance if present
    vehicle = instance.vehicle or Vehicle.objects.filter(plate_number__iexact=plate).first()

    # Link sighting to vehicle if we found one (avoid clearing to None)
    if vehicle:
        if instance.vehicle_id != vehicle.id:
            Sighting.objects.filter(pk=instance.pk).update(vehicle=vehicle)
        vehicle.last_seen = instance.timestamp
        vehicle.save(update_fields=["last_seen"])

    # If vehicle is suspicious/stolen, create alert
    matched_status = None
    if vehicle and vehicle.status in (Vehicle.STATUS_SUSPICIOUS, Vehicle.STATUS_STOLEN):
        matched_status = vehicle.status

    if matched_status:
        # Predict simple next position and route
        route_path = predict_route(
            instance.latitude,
            instance.longitude,
            instance.heading_deg,
            instance.speed_kmh,
            steps=10,
            step_seconds=30,
        )
        predicted = route_path[0] if route_path else {"lat": instance.latitude, "lon": instance.longitude}

        # Save predicted route snapshot
        PredictedRoute.objects.create(
            plate_number=plate,
            path=route_path,
            generated_at=timezone.now(),
        )

        # Create alert
        Alert.objects.create(
            plate_number=plate,
            vehicle=vehicle,
            status=matched_status,
            timestamp=timezone.now(),
            predicted_latitude=predicted.get("lat"),
            predicted_longitude=predicted.get("lon"),
            message=f"Match on {matched_status.upper()} vehicle {plate}",
        )