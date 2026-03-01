from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Job(models.Model):
    """Enhanced Job model for dynamic job recommendations with proper indexing"""
    
    # Job details
    title = models.CharField(max_length=200, db_index=True)
    company = models.CharField(max_length=200, db_index=True)
    location = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    salary_min = models.IntegerField(blank=True, null=True)  # Min salary in thousands
    salary_max = models.IntegerField(blank=True, null=True)  # Max salary in thousands
    
    job_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('internship', 'Internship'),
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
        ],
        default='full_time',
        db_index=True
    )
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('entry', 'Entry Level'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior Level'),
            ('lead', 'Lead Level'),
            ('executive', 'Executive'),
        ],
        default='mid',
        db_index=True
    )
    
    # Enhanced skill data for dynamic matching
    required_skills = models.JSONField(default=list, blank=True)  # List of required skill names
    preferred_skills = models.JSONField(default=list, blank=True)  # List of preferred skill names
    skill_keywords = models.JSONField(default=list, blank=True)  # Extracted keywords
    skill_weights = models.JSONField(default=dict, blank=True)  # Skill importance weights
    feature_vector = models.JSONField(default=list, blank=True)  # ML feature vector
    
    # Dynamic matching fields
    skill_count = models.IntegerField(default=0)  # Total number of required skills
    complexity_score = models.FloatField(default=0.0)  # Job complexity based on requirements
    match_threshold = models.FloatField(default=30.0)  # Minimum match percentage to show
    
    # Metadata
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)  # For promoted jobs
    application_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    match_count = models.IntegerField(default=0)  # How many times this job was recommended
    
    # External job info
    external_url = models.URLField(blank=True, null=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    company_website = models.URLField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(blank=True, null=True)
    last_matched_at = models.DateTimeField(blank=True, null=True)  # Last time this job was in recommendations
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Primary indexes for performance
            models.Index(fields=['title', 'location'], name='idx_job_title_location'),
            models.Index(fields=['company', 'is_active'], name='idx_company_active'),
            models.Index(fields=['job_type', 'experience_level'], name='idx_job_type_exp'),
            models.Index(fields=['is_active', 'created_at'], name='idx_active_created'),
            
            # Skill matching indexes
            models.Index(fields=['skill_count', 'match_threshold'], name='idx_skill_threshold'),
            models.Index(fields=['complexity_score'], name='idx_complexity'),
            models.Index(fields=['match_count'], name='idx_match_count'),
            
            # JSON field indexes for PostgreSQL
            models.Index(fields=['required_skills'], name='idx_required_skills'),
            models.Index(fields=['preferred_skills'], name='idx_preferred_skills'),
            
            # Composite indexes for common queries
            models.Index(fields=['location', 'job_type', 'is_active'], name='idx_location_type_active'),
            models.Index(fields=['experience_level', 'is_active'], name='idx_exp_level_active'),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate dynamic fields"""
        # Calculate skill count
        self.skill_count = len(self.required_skills) if self.required_skills else 0
        
        # Calculate complexity score based on requirements
        complexity = 0.0
        if self.skill_count > 0:
            complexity += min(self.skill_count * 5, 40)  # Max 40 points for skills
        if self.experience_level == 'senior':
            complexity += 20
        elif self.experience_level == 'lead':
            complexity += 25
        elif self.experience_level == 'executive':
            complexity += 30
        if self.requirements and len(self.requirements) > 200:
            complexity += 10
        if self.responsibilities and len(self.responsibilities) > 200:
            complexity += 10
        
        self.complexity_score = min(complexity, 100)
        
        super().save(*args, **kwargs)
    
    def increment_view_count(self):
        """Increment job view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_application_count(self):
        """Increment application count"""
        self.application_count += 1
        self.save(update_fields=['application_count'])
    
    def increment_match_count(self):
        """Increment match count for recommendation analytics"""
        self.match_count += 1
        self.last_matched_at = timezone.now()
        self.save(update_fields=['match_count', 'last_matched_at'])
    
    def calculate_skill_match(self, candidate_skills):
        """Calculate skill match percentage with candidate skills"""
        if not self.required_skills or not candidate_skills:
            return 0.0
        
        candidate_skill_set = set(skill.lower() for skill in candidate_skills)
        required_skill_set = set(skill.lower() for skill in self.required_skills)
        
        if not required_skill_set:
            return 0.0
        
        # Calculate required skills match
        matched_required = len(candidate_skill_set & required_skill_set)
        required_match_percentage = (matched_required / len(required_skill_set)) * 70  # 70% weight
        
        # Calculate preferred skills match (bonus)
        if self.preferred_skills:
            preferred_skill_set = set(skill.lower() for skill in self.preferred_skills)
            matched_preferred = len(candidate_skill_set & preferred_skill_set)
            preferred_match_percentage = (matched_preferred / len(preferred_skill_set)) * 30  # 30% weight
        else:
            preferred_match_percentage = 0
        
        total_match = required_match_percentage + preferred_match_percentage
        return min(total_match, 100.0)
    
    def get_matching_candidates(self, min_match_percentage=30.0):
        """Get candidates that match this job above threshold"""
        from resumes.models import Resume, SkillProfile
        
        matching_candidates = []
        
        # Get all active resumes with extracted skills
        resumes = Resume.objects.filter(
            processing_status='completed',
            extracted_skills__isnull=False
        ).select_related('user')
        
        for resume in resumes:
            match_percentage = self.calculate_skill_match(resume.extracted_skills)
            if match_percentage >= min_match_percentage:
                matching_candidates.append({
                    'resume': resume,
                    'user': resume.user,
                    'match_percentage': match_percentage,
                    'matched_skills': list(set(resume.extracted_skills) & set(self.required_skills)),
                    'missing_skills': list(set(self.required_skills) - set(resume.extracted_skills))
                })
        
        # Sort by match percentage descending
        matching_candidates.sort(key=lambda x: x['match_percentage'], reverse=True)
        return matching_candidates


class JobCategory(models.Model):
    """Job categories for better organization"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    
    def __str__(self):
        return self.name


class JobSkill(models.Model):
    """Individual skills with importance levels"""
    
    SKILL_IMPORTANCE = [
        ('required', 'Required'),
        ('preferred', 'Preferred'),
        ('bonus', 'Bonus'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, blank=True, null=True)  # technical, soft, domain
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name


class JobSkillRequirement(models.Model):
    """Many-to-many relationship between jobs and skills with importance levels"""
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='skill_requirements')
    skill = models.ForeignKey(JobSkill, on_delete=models.CASCADE)
    importance = models.CharField(max_length=20, choices=JobSkill.SKILL_IMPORTANCE, default='required')
    experience_years = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['job', 'skill']
    
    def __str__(self):
        return f"{self.job.title} - {self.skill.name} ({self.importance})"


class JobMatch(models.Model):
    """Enhanced job-resume match results for dynamic recommendations and analytics"""
    
    resume = models.ForeignKey('resumes.Resume', on_delete=models.CASCADE, related_name='job_matches')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='resume_matches')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_recommendations', null=True, blank=True)
    
    # Match scores (0-100)
    overall_score = models.FloatField(default=0.0, db_index=True)
    skills_match_score = models.FloatField(default=0.0)
    experience_match_score = models.FloatField(default=0.0)
    education_match_score = models.FloatField(default=0.0)
    location_match_score = models.FloatField(default=0.0)
    salary_match_score = models.FloatField(default=0.0)
    
    # NEW: Additional scoring components
    projects_match_score = models.FloatField(default=0.0)
    certification_match_score = models.FloatField(default=0.0)
    structure_match_score = models.FloatField(default=0.0)
    achievement_match_score = models.FloatField(default=0.0)
    
    # Detailed match breakdown
    matched_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    additional_skills = models.JSONField(default=list, blank=True)
    skill_match_details = models.JSONField(default=dict, blank=True)  # {skill: match_percentage}
    
    # Recommendation metadata
    match_reason = models.TextField(blank=True, null=True)
    recommendation_rank = models.IntegerField(default=0, db_index=True)
    confidence_level = models.FloatField(default=0.0)  # How confident we are in this match
    
    # User interaction tracking
    is_viewed = models.BooleanField(default=False)
    is_applied = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(blank=True, null=True)
    applied_at = models.DateTimeField(blank=True, null=True)
    saved_at = models.DateTimeField(blank=True, null=True)
    
    # Recommendation context
    recommendation_source = models.CharField(
        max_length=20,
        choices=[
            ('skill_match', 'Skill Match'),
            ('ml_model', 'ML Model'),
            ('collaborative', 'Collaborative'),
            ('content_based', 'Content Based'),
            ('hybrid', 'Hybrid'),
        ],
        default='skill_match'
    )
    
    # Analytics and performance
    click_through_rate = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)
    recommendation_age_days = models.IntegerField(default=0)  # How old is this recommendation
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True)  # When this recommendation expires
    
    class Meta:
        unique_together = ['resume', 'job', 'user']
        ordering = ['-overall_score']
        indexes = [
            # Performance indexes for recommendations
            models.Index(fields=['user', 'overall_score'], name='idx_user_score'),
            models.Index(fields=['resume', 'overall_score'], name='idx_resume_score'),
            models.Index(fields=['job', 'overall_score'], name='idx_job_score'),
            
            # Filtering indexes
            models.Index(fields=['user', 'is_viewed', 'is_applied'], name='idx_user_interactions'),
            models.Index(fields=['recommendation_source', 'created_at'], name='idx_source_created'),
            models.Index(fields=['overall_score', 'created_at'], name='idx_score_created'),
            
            # Expiration and freshness
            models.Index(fields=['expires_at'], name='idx_expires'),
            models.Index(fields=['recommendation_age_days'], name='idx_rec_age'),
        ]
    
    def __str__(self):
        return f"Match: {self.resume.title} -> {self.job.title} ({self.overall_score}%)"
    
    def save(self, *args, **kwargs):
        """Override save to calculate dynamic fields"""
        if not self.pk:  # New match
            # Calculate recommendation age
            from django.utils import timezone
            self.recommendation_age_days = 0
            
            # Set expiration (30 days from creation)
            import datetime
            self.expires_at = timezone.now() + datetime.timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def mark_viewed(self):
        """Mark this recommendation as viewed"""
        from django.utils import timezone
        self.is_viewed = True
        self.viewed_at = timezone.now()
        self.save(update_fields=['is_viewed', 'viewed_at'])
    
    def mark_applied(self):
        """Mark this recommendation as applied"""
        from django.utils import timezone
        self.is_applied = True
        self.applied_at = timezone.now()
        self.save(update_fields=['is_applied', 'applied_at'])
    
    def mark_saved(self):
        """Mark this recommendation as saved"""
        from django.utils import timezone
        self.is_saved = True
        self.saved_at = timezone.now()
        self.save(update_fields=['is_saved', 'saved_at'])
    
    def is_expired(self):
        """Check if this recommendation has expired"""
        from django.utils import timezone
        return self.expires_at and timezone.now() > self.expires_at
    
    def update_age(self):
        """Update the age of this recommendation"""
        from django.utils import timezone
        if self.created_at:
            age = timezone.now() - self.created_at
            self.recommendation_age_days = age.days
            self.save(update_fields=['recommendation_age_days'])
    
    @classmethod
    def get_user_recommendations(cls, user, limit=10, min_score=30.0):
        """Get active recommendations for a user"""
        from django.utils import timezone
        
        return cls.objects.filter(
            user=user,
            overall_score__gte=min_score,
            expires_at__gt=timezone.now()
        ).select_related('job', 'resume').order_by('-overall_score')[:limit]
    
    @classmethod
    def get_job_recommendations(cls, job, limit=50, min_score=30.0):
        """Get candidates that match a job"""
        from django.utils import timezone
        
        return cls.objects.filter(
            job=job,
            overall_score__gte=min_score,
            expires_at__gt=timezone.now()
        ).select_related('user', 'resume').order_by('-overall_score')[:limit]
