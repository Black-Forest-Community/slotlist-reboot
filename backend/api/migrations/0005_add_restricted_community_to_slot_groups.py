# Generated manually for slotlist-reboot

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_add_registration_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='missionslotgroup',
            name='restricted_community',
            field=models.ForeignKey(
                blank=True,
                db_column='restrictedCommunityUid',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='restricted_slot_groups',
                to='api.community'
            ),
        ),
    ]
