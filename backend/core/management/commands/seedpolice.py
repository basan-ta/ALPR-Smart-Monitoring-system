from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    PoliceVehicleRegistration,
    StolenVehicleReport,
    OwnerWatchlist,
)


class Command(BaseCommand):
    help = "Seed police database with sample registrations, stolen reports, and watchlist entries"

    def handle(self, *args, **options):
        # Registrations
        reg1, _ = PoliceVehicleRegistration.objects.get_or_create(
            registration_id='REG-0001',
            defaults={
                'plate_number': 'BA 12 PA 3456',
                'make': 'Toyota',
                'model': 'Corolla',
                'owner_name': 'Ram Bahadur',
                'region_code': 'BA',
                'registered_at': timezone.now(),
            },
        )
        reg2, _ = PoliceVehicleRegistration.objects.get_or_create(
            registration_id='REG-0002',
            defaults={
                'plate_number': 'KO 34 KA 7890',
                'make': 'Honda',
                'model': 'Civic',
                'owner_name': 'Sita Devi',
                'region_code': 'KO',
                'registered_at': timezone.now(),
            },
        )

        # Stolen report (recent)
        StolenVehicleReport.objects.get_or_create(
            case_number='CASE-1001',
            defaults={
                'plate_number': reg2.plate_number,
                'registration': reg2,
                'report_timestamp': timezone.now(),
                'status': StolenVehicleReport.STATUS_OPEN,
                'region_code': reg2.region_code,
                'details': 'Reported stolen near Pokhara',
            },
        )

        # Watchlist owner
        OwnerWatchlist.objects.get_or_create(
            owner_name='Ram Bahadur',
            defaults={'reason': 'Under investigation', 'active': True},
        )

        self.stdout.write(self.style.SUCCESS('Seeded police records successfully'))