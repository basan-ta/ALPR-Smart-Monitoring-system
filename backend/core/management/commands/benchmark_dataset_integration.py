import json
import time
from typing import Dict, Any

from django.core.management.base import BaseCommand, CommandError

from core.models import Vehicle, Sighting, Alert


class Command(BaseCommand):
    help = "Benchmark dataset import vs DB queries to capture performance metrics."

    def add_arguments(self, parser):
        parser.add_argument('--dataset-path', type=str, help='Optional path to dataset JSON to measure read time')
        parser.add_argument('--output', type=str, required=True, help='Path to write benchmark metrics JSON')

    def handle(self, *args, **options):
        dataset_path = options.get('dataset_path')
        output = options['output']

        metrics: Dict[str, Any] = {}

        # Measure JSON read time if dataset provided
        if dataset_path:
            start = time.perf_counter()
            try:
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                metrics['json_read_time_ms'] = round((time.perf_counter() - start) * 1000, 2)
                metrics['json_counts'] = {
                    'vehicles': len(payload.get('vehicles', [])),
                    'sightings': len(payload.get('sightings', [])),
                    'alerts': len(payload.get('alerts', [])),
                }
            except Exception as e:
                raise CommandError(f"Failed to read dataset at {dataset_path}: {e}")

        # DB counts
        start = time.perf_counter(); vcount = Vehicle.objects.count(); metrics['db_vehicle_count_time_ms'] = round((time.perf_counter() - start) * 1000, 2)
        start = time.perf_counter(); scount = Sighting.objects.count(); metrics['db_sighting_count_time_ms'] = round((time.perf_counter() - start) * 1000, 2)
        start = time.perf_counter(); acount = Alert.objects.count(); metrics['db_alert_count_time_ms'] = round((time.perf_counter() - start) * 1000, 2)

        metrics['db_counts'] = {'vehicles': vcount, 'sightings': scount, 'alerts': acount}

        # Plate-based lookup timings (sample up to 50 plates)
        sample_plates = list(Vehicle.objects.values_list('plate_number', flat=True)[:50])
        lookups = []
        for plate in sample_plates:
            start = time.perf_counter(); _ = Vehicle.objects.filter(plate_number=plate).first(); t1 = round((time.perf_counter() - start) * 1000, 2)
            start = time.perf_counter(); _ = list(Sighting.objects.filter(plate_number=plate)[:10]); t2 = round((time.perf_counter() - start) * 1000, 2)
            start = time.perf_counter(); _ = list(Alert.objects.filter(plate_number=plate)[:10]); t3 = round((time.perf_counter() - start) * 1000, 2)
            lookups.append({'plate': plate, 'vehicle_ms': t1, 'sightings_ms': t2, 'alerts_ms': t3})

        metrics['plate_lookup_samples'] = lookups

        try:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise CommandError(f"Failed to write benchmark metrics to {output}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Benchmark complete. Results saved to {output}"))