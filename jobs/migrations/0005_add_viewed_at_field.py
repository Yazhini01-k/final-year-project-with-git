# Generated manually to add viewed_at field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_add_final_jobmatch_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobmatch',
            name='viewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
