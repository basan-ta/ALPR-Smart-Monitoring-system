import json
from typing import List, Dict, Any

from django.core.management.base import BaseCommand, CommandError

from core.models import Vehicle, Sighting, Alert


class Command(BaseCommand):
    help = "Backup core backend data (vehicles, sightings, alerts) to a JSON file for rollback."

    def add_arguments(self, parser):
        parser.add_argument('--output', type=str, required=True, help='Path to write backup JSON')

    def handle(self, *args, **options):
        output = options['output']

        # Collect data
        vehicles_payload: List[Dict[str, Any]] = []
        for v in Vehicle.objects.all().order_by('plate_number'):
            vehicles_payload.append({
                'plate_number': v.plate_number,
                'status': v.status,
                'owner': v.owner,
                'last_seen': v.last_seen.isoformat() if v.last_seen else None,
                'notes': v.notes,
            })

        sightings_payload: List[Dict[str, Any]] = []
        for s in Sighting.objects.all().order_by('timestamp')[:50000]:  # cap to avoid overly large backups
            sightings_payload.append({
                'plate_number': s.plate_number,
                'vehicle_type': s.vehicle_type,
                'color': s.color,
                'latitude': s.latitude,
                'longitude': s.longitude,
                'speed_kmh': s.speed_kmh,
                'heading_deg': s.heading_deg,
                'timestamp': s.timestamp.isoformat() if s.timestamp else None,
            })

        alerts_payload: List[Dict[str, Any]] = []
        for a in Alert.objects.all().order_by('timestamp')[:50000]:
            alerts_payload.append({
                'plate_number': a.plate_number,
                'status': a.status,
                'timestamp': a.timestamp.isoformat() if a.timestamp else None,
                'predicted_latitude': a.predicted_latitude,
                'predicted_longitude': a.predicted_longitude,
                'message': a.message,
                'acknowledged': a.acknowledged,
                'dispatched': a.dispatched,
            })

        payload = {
            'vehicles': vehicles_payload,
            'sightings': sightings_payload,
            'alerts': alerts_payload,
            'summary': {
                'vehicles': len(vehicles_payload),
                'sightings': len(sightings_payload),
                'alerts': len(alerts_payload),
            }
        }

        try:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise CommandError(f"Failed to write backup JSON to {output}: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"Backup complete. vehicles={len(vehicles_payload)}, sightings={len(sightings_payload)}, alerts={len(alerts_payload)} -> {output}"
        ))