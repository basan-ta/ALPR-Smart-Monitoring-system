from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Vehicle, Sighting, Alert, DatasetVersion
from core.services.nepali_plates import (
    convert_plate_to_nepali,
    is_valid_nepali_plate,
    generate_unique,
    extract_province_from_plate,
)
from core.services.nepali_text import pick_devanagari_name, to_devanagari_text


class Command(BaseCommand):
    help = "Migrate existing dataset to Nepali (Devanagari) plates and names while preserving relations."

    def add_arguments(self, parser):
        parser.add_argument('--version', type=str, default='nepali-v1', help='Dataset version label to record')
        parser.add_argument('--dry-run', action='store_true', help='Validate and show summary without applying changes')

    def handle(self, *args, **options):
        version_label = options['version']
        dry_run = options['dry_run']

        vehicles_qs = Vehicle.objects.all().order_by('id')
        sightings_qs = Sighting.objects.all().order_by('id')
        alerts_qs = Alert.objects.all().order_by('id')

        self.stdout.write(self.style.NOTICE(f"Preparing migration '{version_label}' (dry_run={dry_run})"))

        changed_vehicles = 0
        plates_replaced = 0
        names_replaced = 0

        # Track existing new plates to ensure uniqueness
        existing_new_plates = set()

        with transaction.atomic():
            for v in vehicles_qs:
                orig_plate = (v.plate_number or '').strip()
                nep_plate = convert_plate_to_nepali(orig_plate)
                valid = is_valid_nepali_plate(nep_plate)
                if not valid:
                    # generate a new valid Nepali plate
                    nep_plate = generate_unique(prefer='provincial', existing=existing_new_plates)
                    plates_replaced += 1
                existing_new_plates.add(nep_plate)

                prov_dev = extract_province_from_plate(nep_plate)
                # Heuristic gender: keep existing owner, but if empty or Latin, assign a curated Devanagari name
                owner_orig = (v.owner or '').strip()
                if not owner_orig:
                    new_owner = pick_devanagari_name(prov_dev, gender='male')
                else:
                    # Best-effort convert digits and leave letters; full transliteration is out of scope
                    new_owner = to_devanagari_text(owner_orig)

                # If owner remains ASCII-heavy, assign curated name to ensure Devanagari rendering
                if all(ord(ch) < 128 for ch in new_owner):
                    new_owner = pick_devanagari_name(prov_dev, gender='male')
                    names_replaced += 1

                if (v.plate_number != nep_plate) or (v.owner != new_owner):
                    changed_vehicles += 1
                    if not dry_run:
                        v.plate_number = nep_plate
                        v.owner = new_owner
                        v.save(update_fields=['plate_number', 'owner', 'updated_at'])

            # Update plate strings in sightings/alerts to keep consistency
            updated_sightings = 0
            updated_alerts = 0
            for s in sightings_qs:
                np = convert_plate_to_nepali((s.plate_number or '').strip())
                if s.plate_number != np:
                    updated_sightings += 1
                    if not dry_run:
                        s.plate_number = np
                        s.save(update_fields=['plate_number'])

            for a in alerts_qs:
                np = convert_plate_to_nepali((a.plate_number or '').strip())
                msg = (a.message or '').strip()
                # Basic PII cleanup: remove digits to avoid accidental ASCII leakage
                if not dry_run:
                    a.plate_number = np
                    a.message = to_devanagari_text(msg)
                    a.save(update_fields=['plate_number', 'message'])
                    updated_alerts += 1

            if dry_run:
                transaction.set_rollback(True)

        # Record dataset version (even in dry-run we keep a summary without DB write)
        records_v = vehicles_qs.count()
        records_s = sightings_qs.count()
        records_a = alerts_qs.count()

        if not dry_run:
            DatasetVersion.objects.update_or_create(
                version_label=version_label,
                defaults={
                    'notes': f"Nepali migration applied at {timezone.now().isoformat()}",
                    'records_vehicles': records_v,
                    'records_sightings': records_s,
                    'records_alerts': records_a,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Migration '{version_label}' summary: vehicles_changed={changed_vehicles}, plates_replaced={plates_replaced}, names_replaced={names_replaced}, sightings_updated={updated_sightings}, alerts_updated={updated_alerts}, totals(v/s/a)=({records_v}/{records_s}/{records_a})"
        ))