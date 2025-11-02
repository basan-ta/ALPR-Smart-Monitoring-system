import json
from datetime import datetime
from typing import Dict, Any, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Vehicle, Sighting, Alert, DatasetVersion
from core.services.nepali_plates import convert_plate_to_nepali, is_valid_nepali_plate
from core.services.nepali_text import to_devanagari_text


def parse_dt(val: str):
    if not val:
        return None
    try:
        # Accept both Z and offset formats
        return datetime.fromisoformat(val.replace('Z', '+00:00'))
    except Exception:
        return None


class Command(BaseCommand):
    help = "Import consolidated frontend dataset JSON into backend DB (vehicles, sightings, alerts)."

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=True, help='Path to consolidated dataset JSON')
        parser.add_argument('--dataset-version', type=str, default='frontend-import', help='Dataset version label to record')
        parser.add_argument('--dry-run', action='store_true', help='Validate and show summary without applying changes')

    def handle(self, *args, **options):
        path = options['path']
        version_label = options['dataset_version']
        dry_run = options['dry_run']

        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception as e:
            raise CommandError(f"Failed to read JSON at {path}: {e}")

        # Basic structure validation
        vehicles: List[Dict[str, Any]] = payload.get('vehicles') or []
        sightings: List[Dict[str, Any]] = payload.get('sightings') or []
        alerts: List[Dict[str, Any]] = payload.get('alerts') or []

        if not isinstance(vehicles, list) or not isinstance(sightings, list) or not isinstance(alerts, list):
            raise CommandError('Invalid dataset structure: expected lists for vehicles, sightings, alerts')

        # Pre-validation and normalization pass
        invalid_plates = 0
        normalized_vehicles = []
        for v in vehicles:
            plate_raw = v.get('plate_number', '')
            plate = convert_plate_to_nepali(plate_raw)
            owner = to_devanagari_text(v.get('owner', ''))
            status = (v.get('status') or Vehicle.STATUS_NORMAL).strip().lower()
            if status not in {Vehicle.STATUS_NORMAL, Vehicle.STATUS_SUSPICIOUS, Vehicle.STATUS_STOLEN}:
                status = Vehicle.STATUS_NORMAL
            last_seen = parse_dt(v.get('last_seen'))
            if not is_valid_nepali_plate(plate):
                invalid_plates += 1
            normalized_vehicles.append({
                'plate_number': plate,
                'owner': owner,
                'status': status,
                'last_seen': last_seen,
                'notes': v.get('notes', ''),
            })

        normalized_sightings = []
        for s in sightings:
            plate = convert_plate_to_nepali(s.get('plate_number', ''))
            normalized_sightings.append({
                'plate_number': plate,
                'vehicle_type': s.get('vehicle_type', ''),
                'color': s.get('color', ''),
                'latitude': float(s.get('latitude', 0.0)),
                'longitude': float(s.get('longitude', 0.0)),
                'speed_kmh': float(s.get('speed_kmh', 0.0)),
                'heading_deg': float(s.get('heading_deg', 0.0)),
                'timestamp': parse_dt(s.get('timestamp')),
            })

        normalized_alerts = []
        for a in alerts:
            plate = convert_plate_to_nepali(a.get('plate_number', ''))
            status = (a.get('status') or Vehicle.STATUS_NORMAL).strip().lower()
            if status not in {Vehicle.STATUS_NORMAL, Vehicle.STATUS_SUSPICIOUS, Vehicle.STATUS_STOLEN}:
                status = Vehicle.STATUS_NORMAL
            normalized_alerts.append({
                'plate_number': plate,
                'status': status,
                'timestamp': parse_dt(a.get('timestamp')),
                'predicted_latitude': a.get('predicted_latitude'),
                'predicted_longitude': a.get('predicted_longitude'),
                'message': to_devanagari_text(a.get('message', '')),
                'acknowledged': bool(a.get('acknowledged', False)),
                'dispatched': bool(a.get('dispatched', False)),
            })

        self.stdout.write(self.style.NOTICE(f"Dataset summary: vehicles={len(normalized_vehicles)}, sightings={len(normalized_sightings)}, alerts={len(normalized_alerts)}"))
        if invalid_plates:
            self.stdout.write(self.style.WARNING(f"Vehicles with invalid Nepali plate format: {invalid_plates}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry-run complete. No changes applied."))
            return

        # Apply import
        with transaction.atomic():
            # Upsert vehicles by plate_number
            plate_to_vehicle: Dict[str, Vehicle] = {}
            for v in normalized_vehicles:
                plate = v['plate_number']
                obj, created = Vehicle.objects.get_or_create(
                    plate_number=plate,
                    defaults={
                        'status': v['status'],
                        'owner': v['owner'],
                        'last_seen': v['last_seen'],
                        'notes': v.get('notes', ''),
                    }
                )
                if not created:
                    # Update existing record
                    obj.status = v['status']
                    if v['owner']:
                        obj.owner = v['owner']
                    if v['last_seen']:
                        obj.last_seen = v['last_seen']
                    obj.notes = v.get('notes', obj.notes)
                    obj.save()
                plate_to_vehicle[plate] = obj

            # Insert sightings
            created_sightings = 0
            for s in normalized_sightings:
                veh = plate_to_vehicle.get(s['plate_number'])
                Sighting.objects.create(
                    plate_number=s['plate_number'],
                    vehicle=veh,
                    vehicle_type=s.get('vehicle_type', ''),
                    color=s.get('color', ''),
                    latitude=s['latitude'],
                    longitude=s['longitude'],
                    speed_kmh=s['speed_kmh'],
                    heading_deg=s['heading_deg'],
                    timestamp=s['timestamp'] or datetime.utcnow(),
                )
                created_sightings += 1

            # Insert alerts
            created_alerts = 0
            for a in normalized_alerts:
                veh = plate_to_vehicle.get(a['plate_number'])
                Alert.objects.create(
                    plate_number=a['plate_number'],
                    vehicle=veh,
                    status=a['status'],
                    timestamp=a['timestamp'] or datetime.utcnow(),
                    predicted_latitude=a.get('predicted_latitude'),
                    predicted_longitude=a.get('predicted_longitude'),
                    message=a.get('message', ''),
                    acknowledged=a.get('acknowledged', False),
                    dispatched=a.get('dispatched', False),
                )
                created_alerts += 1

            # Record dataset version
            DatasetVersion.objects.update_or_create(
                version_label=version_label,
                defaults={
                    'notes': f'Imported from {path}',
                    'records_vehicles': len(normalized_vehicles),
                    'records_sightings': created_sightings,
                    'records_alerts': created_alerts,
                }
            )

        self.stdout.write(self.style.SUCCESS(
            f"Import complete. vehicles={len(normalized_vehicles)}, sightings={created_sightings}, alerts={created_alerts}"
        ))