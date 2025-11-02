import random
import time
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Vehicle, Sighting
from core.services.nepali_plates import generate_unique, extract_province_from_plate
from core.services.nepali_text import pick_devanagari_name


NEPALI_POOL = []


def ensure_nepali_pool(pool_size: int = 10, prefer: str = 'provincial'):
    """Create a fixed pool of Nepali-format plates with Devanagari owner names.

    Rough status distribution: normal 80%, suspicious 15%, stolen 5%.
    """
    global NEPALI_POOL
    if NEPALI_POOL:
        return NEPALI_POOL

    existing = set(Vehicle.objects.values_list('plate_number', flat=True))

    def pick_status():
        r = random.random()
        if r < 0.05:
            return Vehicle.STATUS_STOLEN
        if r < 0.20:
            return Vehicle.STATUS_SUSPICIOUS
        return Vehicle.STATUS_NORMAL

    for _ in range(max(1, int(pool_size))):
        plate = generate_unique(prefer=prefer, existing=existing)
        existing.add(plate)
        prov = extract_province_from_plate(plate)
        gender = random.choice(['male', 'female'])
        owner = pick_devanagari_name(prov, gender=gender)
        status = pick_status()

        v, created = Vehicle.objects.get_or_create(
            plate_number=plate,
            defaults={'status': status, 'owner': owner, 'notes': 'Simulator pool'}
        )
        if not created:
            changed = False
            if v.owner.strip() == '' or all(ord(ch) < 128 for ch in v.owner):
                v.owner = owner
                changed = True
            if v.status != status:
                v.status = status
                changed = True
            if changed:
                v.save(update_fields=['owner', 'status'])
        NEPALI_POOL.append(v.plate_number)

    return NEPALI_POOL


def random_coord():
    # Roughly around Kathmandu for demo; adjust as needed
    lat = 27.7172 + random.uniform(-0.03, 0.03)
    lon = 85.3240 + random.uniform(-0.03, 0.03)
    return lat, lon


class Command(BaseCommand):
    help = 'Runs a continuous simulator generating vehicle sightings.'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=float, default=2.0, help='Seconds between sightings')
        parser.add_argument('--pool-size', type=int, default=10, help='Number of unique Nepali plates used by simulator')
        parser.add_argument('--prefer', type=str, choices=['provincial', 'legacy'], default='provincial', help='Prefer modern provincial or legacy format')

    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(self.style.SUCCESS('Starting ANPR simulator...'))
        pool_size = int(options.get('pool_size') or 10)
        prefer = options.get('prefer') or 'provincial'
        pool = ensure_nepali_pool(pool_size=pool_size, prefer=prefer)

        while True:
            plate = random.choice(pool)
            lat, lon = random_coord()
            speed = random.uniform(10, 80)
            heading = random.uniform(0, 360)
            color = random.choice(['white', 'black', 'red', 'blue', 'silver'])
            vtype = random.choice(['sedan', 'suv', 'truck', 'van'])

            Sighting.objects.create(
                plate_number=plate,
                vehicle=Vehicle.objects.filter(plate_number__iexact=plate).first(),
                vehicle_type=vtype,
                color=color,
                latitude=lat,
                longitude=lon,
                speed_kmh=speed,
                heading_deg=heading,
                timestamp=timezone.now(),
            )

            self.stdout.write(self.style.NOTICE(f"Sighted {plate} at {lat:.5f},{lon:.5f} speed={speed:.1f} heading={heading:.1f}"))
            time.sleep(interval)