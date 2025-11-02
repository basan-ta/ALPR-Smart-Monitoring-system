from typing import Set

from django.core.management.base import BaseCommand

from core.models import Vehicle, Sighting, Alert
from core.services.nepali_plates import convert_plate_to_nepali, is_valid_nepali_plate


class Command(BaseCommand):
    help = "Purge records with non-Nepali plate formats (e.g., 'KTM001'), keeping only valid Nepali plates and owners."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without applying changes')
        parser.add_argument('--plate', type=str, default='', help='Specific plate to purge (exact match)')

    def handle(self, *args, **options):
        dry = options['dry_run']
        target_plate = (options.get('plate') or '').strip()

        # Build set of invalid plates from Vehicles, Sightings, Alerts
        invalid: Set[str] = set()

        def _maybe_add(p: str):
            if not p:
                return
            nep = convert_plate_to_nepali(p)
            if not is_valid_nepali_plate(nep):
                invalid.add(p)

        if target_plate:
            invalid.add(target_plate)

        for p in Vehicle.objects.values_list('plate_number', flat=True):
            _maybe_add(p)
        for p in Sighting.objects.values_list('plate_number', flat=True).distinct():
            _maybe_add(p)
        for p in Alert.objects.values_list('plate_number', flat=True).distinct():
            _maybe_add(p)

        if not invalid:
            self.stdout.write(self.style.SUCCESS('No non-Nepali plates found to purge.'))
            return

        # Count impacts
        vehicles_qs = Vehicle.objects.filter(plate_number__in=invalid)
        sightings_qs = Sighting.objects.filter(plate_number__in=invalid)
        alerts_qs = Alert.objects.filter(plate_number__in=invalid)

        v_count = vehicles_qs.count()
        s_count = sightings_qs.count()
        a_count = alerts_qs.count()

        self.stdout.write(self.style.NOTICE(
            f"Purging non-Nepali plates: {sorted(list(invalid))}"
        ))
        self.stdout.write(
            f"Impacts => Vehicles: {v_count}, Sightings: {s_count}, Alerts: {a_count}"
        )

        if dry:
            self.stdout.write(self.style.SUCCESS('Dry-run complete. No changes applied.'))
            return

        # Delete in order: sightings, alerts, vehicles
        s_deleted, _ = sightings_qs.delete()
        a_deleted, _ = alerts_qs.delete()
        v_deleted, _ = vehicles_qs.delete()

        self.stdout.write(self.style.SUCCESS(
            f"Purge complete. Deleted -> Vehicles: {v_deleted}, Sightings: {s_deleted}, Alerts: {a_deleted}"
        ))