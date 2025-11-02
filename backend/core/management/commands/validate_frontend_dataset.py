import json
from typing import Dict, Any, List

from django.core.management.base import BaseCommand, CommandError

from core.services.nepali_plates import is_valid_nepali_plate, convert_plate_to_nepali


class Command(BaseCommand):
    help = "Validate consolidated frontend dataset JSON and produce a detailed report."

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=True, help='Path to consolidated dataset JSON')
        parser.add_argument('--output', type=str, required=True, help='Path to save validation report JSON')

    def handle(self, *args, **options):
        path = options['path']
        output = options['output']

        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception as e:
            raise CommandError(f"Failed to read dataset JSON at {path}: {e}")

        vehicles: List[Dict[str, Any]] = payload.get('vehicles') or []
        sightings: List[Dict[str, Any]] = payload.get('sightings') or []
        alerts: List[Dict[str, Any]] = payload.get('alerts') or []

        if not isinstance(vehicles, list) or not isinstance(sightings, list) or not isinstance(alerts, list):
            raise CommandError('Invalid dataset structure: expected lists for vehicles, sightings, alerts')

        # Vehicles validation
        invalid_plates = []
        status_counts = {'normal': 0, 'suspicious': 0, 'stolen': 0, 'other': 0}
        for v in vehicles:
            plate = convert_plate_to_nepali(v.get('plate_number', ''))
            if not is_valid_nepali_plate(plate):
                if len(invalid_plates) < 50:
                    invalid_plates.append(plate)
            status = (v.get('status') or 'normal').strip().lower()
            status_counts[status if status in status_counts else 'other'] += 1

        # Sightings validation
        invalid_coords = []
        for s in sightings:
            lat = float(s.get('latitude', 0.0))
            lon = float(s.get('longitude', 0.0))
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                if len(invalid_coords) < 50:
                    invalid_coords.append({'lat': lat, 'lon': lon})

        # Alerts validation
        alert_status_counts = {'normal': 0, 'suspicious': 0, 'stolen': 0, 'other': 0}
        for a in alerts:
            status = (a.get('status') or 'normal').strip().lower()
            alert_status_counts[status if status in alert_status_counts else 'other'] += 1

        report = {
            'summary': {
                'vehicles': len(vehicles),
                'sightings': len(sightings),
                'alerts': len(alerts),
            },
            'vehicles': {
                'invalid_plates_sample': invalid_plates,
                'status_counts': status_counts,
            },
            'sightings': {
                'invalid_coords_sample': invalid_coords,
            },
            'alerts': {
                'status_counts': alert_status_counts,
            }
        }

        try:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise CommandError(f"Failed to write validation report to {output}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Validation complete. Report saved to {output}"))