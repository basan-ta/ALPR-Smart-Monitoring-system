import random
from typing import List, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Vehicle, Sighting, Alert, PredictedRoute, DatasetVersion
from core.services.nepali_plates import generate_unique, extract_province_from_plate
from core.services.nepali_text import pick_devanagari_name
from core.services.prediction import predict_route


def _random_coord_in_nepal() -> Tuple[float, float]:
    """Return a random lat/lon roughly within Nepal's bounding box.

    Latitude ~ 26.3 to 30.5, Longitude ~ 80.0 to 88.5
    """
    lat = random.uniform(26.3, 30.5)
    lon = random.uniform(80.0, 88.5)
    return lat, lon


class Command(BaseCommand):
    help = "Seed random vehicles and sightings using Nepali (Devanagari) number plate rules"

    def add_arguments(self, parser):
        parser.add_argument('--vehicles', type=int, default=100, help='Number of vehicles to create')
        parser.add_argument('--with-sightings', action='store_true', help='Also create recent sightings for vehicles')
        parser.add_argument('--sightings-per-vehicle', type=int, default=2, help='How many sightings per vehicle when enabled')
        parser.add_argument('--prefer', type=str, choices=['provincial', 'legacy'], default='provincial', help='Prefer modern provincial or legacy format')
        parser.add_argument('--dataset-version', type=str, default='nepali-seed-v1', help='Dataset version label to record')

    def handle(self, *args, **options):
        n = int(options['vehicles'])
        with_sightings = bool(options['with_sightings'])
        sightings_per_vehicle = max(0, int(options['sightings_per_vehicle']))
        prefer = options['prefer'] or 'provincial'
        version_label = options['dataset_version']

        self.stdout.write(self.style.NOTICE(
            f"Seeding {n} vehicles (prefer={prefer}, with_sightings={with_sightings}, spv={sightings_per_vehicle})"
        ))

        created_vehicles = 0
        created_sightings = 0
        created_alerts = 0
        created_routes = 0

        existing = set(Vehicle.objects.values_list('plate_number', flat=True))

        # Status distribution: normal 80%, suspicious 15%, stolen 5%
        def pick_status() -> str:
            r = random.random()
            if r < 0.05:
                return Vehicle.STATUS_STOLEN
            if r < 0.20:
                return Vehicle.STATUS_SUSPICIOUS
            return Vehicle.STATUS_NORMAL

        with transaction.atomic():
            vehicles: List[Vehicle] = []
            for _ in range(n):
                plate = generate_unique(prefer=prefer, existing=existing)
                existing.add(plate)
                prov_dev = extract_province_from_plate(plate)
                # Skew gender randomly; name pool picks culturally aligned surnames by province when available
                gender = random.choice(['male', 'female'])
                owner = pick_devanagari_name(prov_dev, gender=gender)
                status = pick_status()

                v = Vehicle.objects.create(
                    plate_number=plate,
                    status=status,
                    owner=owner,
                    last_seen=None,
                    notes='',
                )
                vehicles.append(v)
                created_vehicles += 1

            # Optionally create sightings and derived artifacts
            if with_sightings and sightings_per_vehicle > 0:
                now = timezone.now()
                for v in vehicles:
                    # Create N recent sightings with small movement
                    lat, lon = _random_coord_in_nepal()
                    heading = random.uniform(0, 360)
                    speed = random.uniform(10, 80)  # km/h
                    for i in range(sightings_per_vehicle):
                        # Slight movement per sighting
                        dlat = random.uniform(-0.01, 0.01)
                        dlon = random.uniform(-0.01, 0.01)
                        ts = now - timezone.timedelta(minutes=random.randint(0, 90))
                        s = Sighting.objects.create(
                            plate_number=v.plate_number,
                            vehicle=v,
                            vehicle_type='',
                            color='',
                            latitude=lat + dlat,
                            longitude=lon + dlon,
                            speed_kmh=speed,
                            heading_deg=heading,
                            timestamp=ts,
                        )
                        created_sightings += 1
                        # Track last seen
                        if v.last_seen is None or v.last_seen < s.timestamp:
                            v.last_seen = s.timestamp
                            v.save(update_fields=['last_seen', 'updated_at'])

                    # Alerts for suspicious/stolen
                    if v.status in (Vehicle.STATUS_SUSPICIOUS, Vehicle.STATUS_STOLEN):
                        msg = 'चेतावनी: शंकास्पद गतिविधि' if v.status == Vehicle.STATUS_SUSPICIOUS else 'संभावित चोरी गरिएको सवारी'
                        Alert.objects.create(
                            plate_number=v.plate_number,
                            vehicle=v,
                            status=v.status,
                            timestamp=timezone.now(),
                            predicted_latitude=lat,
                            predicted_longitude=lon,
                            message=msg,
                            acknowledged=False,
                            dispatched=False,
                        )
                        created_alerts += 1

                        # Predicted route from latest sighting
                        path = predict_route(lat, lon, heading_deg=heading, speed_kmh=speed, steps=10, step_seconds=30)
                        PredictedRoute.objects.create(
                            plate_number=v.plate_number,
                            path=path,
                            generated_at=timezone.now(),
                        )
                        created_routes += 1

            # Record dataset version summary
            DatasetVersion.objects.update_or_create(
                version_label=version_label,
                defaults={
                    'notes': f"Seeded at {timezone.now().isoformat()} (prefer={prefer})",
                    'records_vehicles': Vehicle.objects.count(),
                    'records_sightings': Sighting.objects.count(),
                    'records_alerts': Alert.objects.count(),
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: vehicles={created_vehicles}, sightings={created_sightings}, alerts={created_alerts}, routes={created_routes}"
        ))