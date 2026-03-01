#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')
django.setup()

from django.db import connection

def check_jobmatch_columns():
    """Check all columns in jobs_jobmatch table"""
    print("🔍 Checking JobMatch table columns...")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'jobs_jobmatch' 
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
    print(f"📊 Found {len(columns)} columns:")
    for col in columns:
        print(f"  - {col[0]} ({col[1]}, nullable={col[2]})")
    
    # Check for specific missing columns
    required_columns = [
        'projects_match_score', 'certification_match_score', 
        'structure_match_score', 'achievement_match_score',
        'is_viewed', 'is_applied', 'is_saved',
        'viewed_at', 'applied_at', 'saved_at',
        'recommendation_source', 'confidence_level',
        'skill_match_details', 'user', 'click_through_rate',
        'conversion_rate', 'expires_at', 'recommendation_age_days',
        'updated_at'
    ]
    
    existing_columns = [col[0] for col in columns]
    missing_columns = [col for col in required_columns if col not in existing_columns]
    
    if missing_columns:
        print(f"\n❌ Missing columns: {missing_columns}")
    else:
        print(f"\n✅ All required columns exist!")
    
    return len(missing_columns) == 0

if __name__ == '__main__':
    success = check_jobmatch_columns()
    if success:
        print("\n🎉 All JobMatch columns are present!")
    else:
        print("\n❌ Some JobMatch columns are missing!")
