import random
import time
from typing import Optional, Tuple

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Vehicle, Sighting, Alert
from core.services.nepali_plates import generate_unique, extract_province_from_plate
from core.services.nepali_text import pick_devanagari_name


PROVINCE_CENTERS = {
    '१': (26.4839, 87.2830),  # Koshi (Biratnagar)
    '२': (26.7161, 85.9216),  # Madhesh (Janakpur)
    '३': (27.7172, 85.3240),  # Bagmati (Kathmandu)
    '४': (28.2096, 83.9856),  # Gandaki (Pokhara)
    '५': (27.6766, 83.4323),  # Lumbini (Butwal)
    '६': (28.6000, 81.6333),  # Karnali (Surkhet)
    '७': (28.7077, 80.5898),  # Sudurpashchim (Dhangadhi)
}


def random_coord_near(center: Tuple[float, float], jitter_deg: float = 0.05) -> Tuple[float, float]:
    lat, lon = center
    return lat + random.uniform(-jitter_deg, jitter_deg), lon + random.uniform(-jitter_deg, jitter_deg)


class Command(BaseCommand):
    help = "Seed random Nepali vehicles with valid plates and Devanagari owner names; optionally generate sightings and alerts."

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=150, help='Number of vehicles to create')
        parser.add_argument('--include-sightings', action='store_true', help='Create random sightings per vehicle')
        parser.add_argument('--include-alerts', action='store_true', help='Create alerts for suspicious/stolen vehicles')
        parser.add_argument('--max-sightings-per-vehicle', type=int, default=3, help='Upper bound sightings per vehicle')

    def handle(self, *args, **options):
        count = max(0, int(options['count']))
        include_s = options['include_sightings']
        include_a = options['include_alerts']
        max_s = max(1, int(options['max_sightings_per_vehicle']))

        created_v = 0
        created_s = 0
        created_a = 0

        self.stdout.write(self.style.NOTICE(
            f"Seeding Nepali vehicles: count={count}, sightings={include_s}, alerts={include_a}"
        ))

        existing = set(Vehicle.objects.values_list('plate_number', flat=True))
        for _ in range(count):
            # Prefer modern provincial format; mix a bit of legacy
            prefer = 'provincial' if random.random() < 0.8 else 'legacy'
            plate = generate_unique(prefer=prefer, existing=existing)
            existing.add(plate)

            # Status distribution
            r = random.random()
            status = Vehicle.STATUS_NORMAL
            if r < 0.08:
                status = Vehicle.STATUS_STOLEN
            elif r < 0.20:
                status = Vehicle.STATUS_SUSPICIOUS

            prov = extract_province_from_plate(plate)
            gender = 'male' if random.random() < 0.6 else 'female'
            owner = pick_devanagari_name(prov, gender)

            v = Vehicle.objects.create(
                plate_number=plate,
                status=status,
                owner=owner,
                notes='',
            )
            created_v += 1

            # Generate sightings
            if include_s:
                center = PROVINCE_CENTERS.get(prov or '३', PROVINCE_CENTERS['३'])
                s_for_v = random.randint(1, max_s)
                now = timezone.now()
                for i in range(s_for_v):
                    lat, lon = random_coord_near(center)
                    speed = random.uniform(10, 80)
                    heading = random.uniform(0, 360)
                    ts = now - timezone.timedelta(seconds=random.randint(60, 3600))
                    Sighting.objects.create(
                        plate_number=plate,
                        vehicle=v,
                        vehicle_type=random.choice(['sedan', 'suv', 'truck', 'van', 'motorcycle']),
                        color=random.choice(['white', 'black', 'red', 'blue', 'silver']),
                        latitude=lat,
                        longitude=lon,
                        speed_kmh=speed,
                        heading_deg=heading,
                        timestamp=ts,
                    )
                    created_s += 1
                    # Track last_seen
                    if (not v.last_seen) or (ts > v.last_seen):
                        v.last_seen = ts
                        v.save(update_fields=['last_seen'])

            # Alerts for flagged vehicles
            if include_a and v.status in (Vehicle.STATUS_SUSPICIOUS, Vehicle.STATUS_STOLEN):
                lat, lon = (None, None)
                last_s = Sighting.objects.filter(vehicle=v).order_by('-timestamp').first()
                if last_s:
                    lat, lon = last_s.latitude, last_s.longitude
                Alert.objects.create(
                    plate_number=plate,
                    vehicle=v,
                    status=v.status,
                    predicted_latitude=lat,
                    predicted_longitude=lon,
                    message=f"Flagged {v.status}",
                )
                created_a += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete. vehicles={created_v}, sightings={created_s}, alerts={created_a}"
        ))