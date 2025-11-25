# Generated manually for slotlist-reboot

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_remove_communityapplication_application_text_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='missionslotregistration',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')],
                default='pending',
                max_length=20
            ),
        ),
    ]
