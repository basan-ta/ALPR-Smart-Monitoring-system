import os
import glob

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Remove legacy dataset files in backend to establish a single source of truth (database)."

    def add_arguments(self, parser):
        parser.add_argument('--dir', type=str, default='data', help='Relative directory under backend to clean')
        parser.add_argument('--dry-run', action='store_true', help='List files to be removed without deleting')

    def handle(self, *args, **options):
        rel_dir = options['dir']
        dry = options['dry_run']
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # core/management/commands -> core
        backend_root = os.path.dirname(base)  # backend
        target_dir = os.path.join(backend_root, rel_dir)

        patterns = [
            os.path.join(target_dir, '*.json'),
            os.path.join(target_dir, '*.csv'),
        ]

        removed = 0
        for pat in patterns:
            for path in glob.glob(pat):
                if dry:
                    self.stdout.write(f"Would remove: {path}")
                else:
                    try:
                        os.remove(path)
                        removed += 1
                        self.stdout.write(f"Removed: {path}")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Failed to remove {path}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Legacy cleanup complete. Files removed: {removed}"))