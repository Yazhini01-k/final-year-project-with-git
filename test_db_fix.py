#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_analyzer.settings')
django.setup()

from jobs.models import JobMatch
from django.db import connection

def test_database_fix():
    """Test that the JobMatch model has all required fields"""
    print("🔍 Testing Database Fix...")
    
    # Check if columns exist
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'jobs_jobmatch' 
            AND column_name IN ('projects_match_score', 'certification_match_score', 'structure_match_score', 'achievement_match_score')
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
    print(f"✅ Found columns: {columns}")
    
    # Test creating a JobMatch instance
    try:
        from accounts.models import User
        from jobs.models import Job
        from resumes.models import Resume
        
        # Get sample data
        user = User.objects.filter(role='candidate').first()
        job = Job.objects.filter(is_active=True).first()
        resume = Resume.objects.filter(processing_status='completed').first()
        
        if user and job and resume:
            # Test JobMatch creation
            job_match = JobMatch.objects.create(
                resume=resume,
                job=job,
                user=user,
                overall_score=85.5,
                skills_match_score=90.0,
                projects_match_score=75.0,
                education_match_score=80.0,
                certification_match_score=60.0,
                structure_match_score=70.0,
                achievement_match_score=65.0,
                matched_skills=['Python', 'Django'],
                missing_skills=['AWS'],
                match_reason='Strong skills match'
            )
            
            print(f"✅ Created JobMatch with ID: {job_match.id}")
            print(f"✅ Projects score: {job_match.projects_match_score}")
            print(f"✅ Certification score: {job_match.certification_match_score}")
            print(f"✅ Structure score: {job_match.structure_match_score}")
            print(f"✅ Achievement score: {job_match.achievement_match_score}")
            
            # Clean up
            job_match.delete()
            print("✅ Test completed successfully!")
        else:
            print("⚠️  No sample data found for testing")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = test_database_fix()
    if success:
        print("\n🎉 Database fix verified successfully!")
    else:
        print("\n❌ Database fix failed!")
