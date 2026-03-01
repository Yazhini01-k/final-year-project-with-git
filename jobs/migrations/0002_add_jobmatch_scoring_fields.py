# Generated manually to fix missing fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        # Add scoring fields
        migrations.AddField(
            model_name='jobmatch',
            name='projects_match_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='certification_match_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='structure_match_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='achievement_match_score',
            field=models.FloatField(default=0.0),
        ),
        
        # Add missing interaction fields
        migrations.AddField(
            model_name='jobmatch',
            name='is_viewed',
            field=models.BooleanField(default=False),
        ),
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
            name='viewed_at',
            field=models.DateTimeField(blank=True, null=True),
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
        
        # Add metadata fields
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
            name='confidence_level',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='skill_match_details',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='user',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='job_recommendations',
                to='accounts.user'
            ),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='click_through_rate',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='conversion_rate',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='recommendation_age_days',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='jobmatch',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
