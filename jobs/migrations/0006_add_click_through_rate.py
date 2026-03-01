# Generated manually to add click_through_rate field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0005_add_viewed_at_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobmatch',
            name='click_through_rate',
            field=models.FloatField(default=0.0),
        ),
    ]
