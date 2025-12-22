from django.core.management.base import BaseCommand
from api.models import Mission, Community
from django.conf import settings


class Command(BaseCommand):
    help = 'Convert relative media URLs to absolute URLs'

    def handle(self, *args, **options):
        backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8022')
        
        # Update mission banner images
        missions_updated = 0
        for mission in Mission.objects.filter(banner_image_url__isnull=False):
            if mission.banner_image_url.startswith('/media/'):
                mission.banner_image_url = f'{backend_url}{mission.banner_image_url}'
                mission.save(update_fields=['banner_image_url'])
                missions_updated += 1
        
        # Update community logos
        communities_updated = 0
        for community in Community.objects.filter(logo_url__isnull=False):
            if community.logo_url.startswith('/media/'):
                community.logo_url = f'{backend_url}{community.logo_url}'
                community.save(update_fields=['logo_url'])
                communities_updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Updated {missions_updated} mission banners and {communities_updated} community logos'
        ))
