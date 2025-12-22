from django.core.management.base import BaseCommand
from api.models import Mission, Community
from api.image_utils import download_and_store_image
from django.conf import settings
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Fix all media URLs and download embedded images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be updated without saving',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8022')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be saved'))
        
        self.stdout.write(f'Backend URL: {backend_url}\n')
        
        # Step 1: Fix banner image URLs
        self.stdout.write(self.style.MIGRATE_HEADING('Step 1: Fixing banner and logo URLs'))
        missions_updated = 0
        for mission in Mission.objects.filter(banner_image_url__isnull=False):
            if mission.banner_image_url.startswith('http://localhost:8022'):
                if not dry_run:
                    mission.banner_image_url = mission.banner_image_url.replace('http://localhost:8022', backend_url)
                    mission.save(update_fields=['banner_image_url'])
                missions_updated += 1
        
        communities_updated = 0
        for community in Community.objects.filter(logo_url__isnull=False):
            if community.logo_url.startswith('http://localhost:8022'):
                if not dry_run:
                    community.logo_url = community.logo_url.replace('http://localhost:8022', backend_url)
                    community.save(update_fields=['logo_url'])
                communities_updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Updated {missions_updated} mission banners and {communities_updated} community logos\n'
        ))
        
        # Step 2: Fix embedded images in text fields
        self.stdout.write(self.style.MIGRATE_HEADING('Step 2: Downloading embedded images'))
        missions_with_images = 0
        images_downloaded = 0
        
        for mission in Mission.objects.all():
            mission_changed = False
            
            html_fields = [
                'detailed_description',
                'collapsed_description',
                'tech_support',
                'rules',
            ]
            
            for field_name in html_fields:
                content = getattr(mission, field_name)
                if not content or 'slotlist-info.storage.googleapis.com' not in content:
                    continue
                
                self.stdout.write(f'Processing {mission.slug} - {field_name}')
                
                soup = BeautifulSoup(content, 'html.parser')
                images = soup.find_all('img')
                
                for img in images:
                    src = img.get('src')
                    if src and 'slotlist-info.storage.googleapis.com' in src:
                        self.stdout.write(f'  Found image: {src[:60]}...')
                        
                        if not dry_run:
                            new_url = download_and_store_image(src, f'missions/{mission.slug}')
                            
                            if new_url:
                                img['src'] = new_url
                                images_downloaded += 1
                                mission_changed = True
                                self.stdout.write(self.style.SUCCESS(f'  → Downloaded'))
                            else:
                                self.stdout.write(self.style.ERROR(f'  → Failed'))
                        else:
                            images_downloaded += 1
                            mission_changed = True
                
                if mission_changed and not dry_run:
                    setattr(mission, field_name, str(soup))
            
            if mission_changed:
                missions_with_images += 1
                if not dry_run:
                    mission.save()
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(self.style.SUCCESS(f'  Banner/Logo URLs updated: {missions_updated + communities_updated}'))
        self.stdout.write(self.style.SUCCESS(f'  Missions with embedded images: {missions_with_images}'))
        self.stdout.write(self.style.SUCCESS(f'  Total images downloaded: {images_downloaded}'))
        self.stdout.write('=' * 60)

