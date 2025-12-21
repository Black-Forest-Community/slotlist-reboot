from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db import models
from api.models import Community, Mission, User, MissionSlotRegistration


class Command(BaseCommand):
    help = 'Remove all communities, missions, users and slot registrations not affiliated with Black Forest [bf] community'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_confirm = options['yes']

        # Find Black Forest community
        try:
            bf_community = Community.objects.get(tag='BF')
            self.stdout.write(f'Found Black Forest community: {bf_community.name} [{bf_community.tag}]')
            self.stdout.write(f'Community UID: {bf_community.uid}')
        except Community.DoesNotExist:
            raise CommandError('Black Forest [BF] community not found in database')
        # Find communities to delete (all except BF)
        communities_to_delete = Community.objects.exclude(uid=bf_community.uid)
        community_count = communities_to_delete.count()

        # Find missions to delete (not affiliated with BF)
        missions_to_delete = Mission.objects.exclude(community=bf_community)
        mission_count = missions_to_delete.count()

        # Find users to delete (not affiliated with BF)
        users_to_delete = User.objects.exclude(community=bf_community)
        user_count = users_to_delete.count()

        # Find slot registrations to delete (registrations for missions not in BF or by users not in BF)
        registrations_to_delete = MissionSlotRegistration.objects.filter(
            models.Q(user__in=users_to_delete) | 
            models.Q(slot__slot_group__mission__in=missions_to_delete)
        )
        registration_count = registrations_to_delete.count()

        # Display what will be deleted
        self.stdout.write('\n=== SUMMARY ===')
        self.stdout.write(f'Communities to delete: {community_count}')
        self.stdout.write(f'Missions to delete: {mission_count}')
        self.stdout.write(f'Users to delete: {user_count}')
        self.stdout.write(f'Slot registrations to delete: {registration_count}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN - No changes will be made'))
            self._preview_deletions(communities_to_delete, missions_to_delete, users_to_delete, registrations_to_delete)
            return

        # Confirm deletion
        if not skip_confirm:
            self.stdout.write(self.style.WARNING(
                f'\nThis will PERMANENTLY DELETE {community_count} communities, {mission_count} missions, '
                f'{user_count} users, and {registration_count} slot registrations!'
            ))
            confirm = input('Type "DELETE" to confirm: ')
            if confirm != 'DELETE':
                self.stdout.write(self.style.ERROR('Deletion cancelled'))
                return

        # Perform deletion in transaction
        try:
            with transaction.atomic():
                self.stdout.write('\nDeleting slot registrations...')
                deleted_registrations = registrations_to_delete.delete()
                
                self.stdout.write('Deleting missions...')
                deleted_missions = missions_to_delete.delete()
                
                self.stdout.write('Deleting users...')
                deleted_users = users_to_delete.delete()
                
                self.stdout.write('Deleting communities...')
                deleted_communities = communities_to_delete.delete()
                
                self.stdout.write(self.style.SUCCESS(
                    f'\nSuccessfully deleted {community_count} communities, {mission_count} missions, '
                    f'{user_count} users, and {registration_count} slot registrations'
                ))
                total_deleted = (deleted_communities[0] + deleted_missions[0] + 
                                deleted_users[0] + deleted_registrations[0])
                self.stdout.write(f'Total database objects deleted: {total_deleted}')
                
        except Exception as e:
            raise CommandError(f'Failed to delete data: {e}')

    def _preview_deletions(self, communities, missions, users, registrations):
        """Preview what would be deleted"""
        self.stdout.write('\n=== COMMUNITIES TO DELETE ===')
        if communities.exists():
            for community in communities[:10]:
                self.stdout.write(f'- {community.name} [{community.tag}]')
            if communities.count() > 10:
                self.stdout.write(f'... and {communities.count() - 10} more')
        else:
            self.stdout.write('No communities to delete')

        self.stdout.write('\n=== MISSIONS TO DELETE ===')
        if missions.exists():
            for mission in missions[:10]:
                community_name = mission.community.name if mission.community else 'No community'
                self.stdout.write(
                    f'- {mission.title} ({mission.slug}) - Community: {community_name}'
                )
            if missions.count() > 10:
                self.stdout.write(f'... and {missions.count() - 10} more')
        else:
            self.stdout.write('No missions to delete')

        self.stdout.write('\n=== USERS TO DELETE ===')
        if users.exists():
            for user in users[:10]:
                community_name = user.community.name if user.community else 'No community'
                self.stdout.write(
                    f'- {user.nickname} ({user.steam_id}) - Community: {community_name}'
                )
            if users.count() > 10:
                self.stdout.write(f'... and {users.count() - 10} more')
        else:
            self.stdout.write('No users to delete')

        self.stdout.write('\n=== SLOT REGISTRATIONS TO DELETE ===')
        if registrations.exists():
            for reg in registrations[:10]:
                mission_title = reg.slot.slot_group.mission.title
                self.stdout.write(
                    f'- {reg.user.nickname} -> {reg.slot.title} (Mission: {mission_title})'
                )
            if registrations.count() > 10:
                self.stdout.write(f'... and {registrations.count() - 10} more')
        else:
            self.stdout.write('No slot registrations to delete')
