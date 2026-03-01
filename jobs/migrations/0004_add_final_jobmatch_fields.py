# Generated manually to add final JobMatch fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_add_remaining_jobmatch_fields'),
    ]

    operations = [
        # Add essential missing fields
        migrations.AddField(
            model_name='jobmatch',
            name='is_applied',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='is_saved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='applied_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='saved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='recommendation_source',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('skill_match', 'Skill Match'),
                    ('ml_model', 'ML Model'),
                    ('collaborative', 'Collaborative'),
                    ('content_based', 'Content Based'),
                    ('hybrid', 'Hybrid'),
                ],
                default='skill_match'
            ),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
