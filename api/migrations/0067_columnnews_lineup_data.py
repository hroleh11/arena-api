# Generated manually for lineup_data field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0066_columnnews_lineup_global_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='columnnews',
            name='lineup_data',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
