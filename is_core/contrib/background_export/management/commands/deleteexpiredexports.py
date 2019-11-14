from django.core.management.base import BaseCommand

from is_core.contrib.background_export.models import ExportedFile


class Command(BaseCommand):

    def handle(self, **options):
        expired_exported_files_qs = ExportedFile.objects.filter_expired()
        count_expired_exported_files = expired_exported_files_qs.count()

        if not count_expired_exported_files:
            self.stdout.write('No expired exported files were found.')
        else:
            [exported_file.file.delete() for exported_file in ExportedFile.objects.filter_expired()]
            self.stdout.write('{} expired exported files was removed.'.format(count_expired_exported_files))
