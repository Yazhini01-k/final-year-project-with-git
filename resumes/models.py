from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Resume(models.Model):
    """Resume model for storing uploaded resumes and extracted data"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='resumes/')
    original_filename = models.CharField(max_length=255)
    
    # Extracted text content
    raw_text = models.TextField(blank=True, null=True)
    processed_text = models.TextField(blank=True, null=True)
    
    # Parsed information
    extracted_skills = models.JSONField(default=list, blank=True)
    extracted_education = models.JSONField(default=list, blank=True)
    extracted_experience = models.JSONField(default=list, blank=True)
    extracted_contact_info = models.JSONField(default=dict, blank=True)
    
    # NEW: Additional extracted information
    extracted_projects = models.JSONField(default=list, blank=True)
    extracted_certificates = models.JSONField(default=list, blank=True)
    extracted_achievements = models.JSONField(default=list, blank=True)
    
    # ML processing data
    feature_vector = models.JSONField(default=list, blank=True)
    skill_keywords = models.JSONField(default=list, blank=True)
    
    # Metadata
    file_size = models.IntegerField(default=0)
    file_type = models.CharField(max_length=10)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    job_match_count = models.IntegerField(default=0)
    matched_jobs = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        """Override save to automatically create/update skill profile when processing is completed"""
        super().save(*args, **kwargs)
        
        # STRICT: Only create skill profile if processing is completed AND we have extracted skills
        if (self.processing_status == 'completed' and 
            self.extracted_skills and 
            len(self.extracted_skills) > 0):
            
            self.create_strict_skill_profile()
    
    def create_strict_skill_profile(self):
        """STRICT: Create or update user's skill profile based ONLY on extracted skills from resume"""
        if not self.extracted_skills:
            return
        
        # Create skills dictionary ONLY from extracted skills
        skills_dict = {}
        for skill in self.extracted_skills:
            if isinstance(skill, str) and skill.strip():
                skills_dict[skill.lower().strip()] = 'intermediate'
        
        if not skills_dict:
            return
        
        # Get or create skill profile
        skill_profile, created = SkillProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'skills': skills_dict,
                'total_skills_count': len(skills_dict)
            }
        )
        
        if not created:
            # Update existing skill profile with new skills ONLY from this resume
            skill_profile.skills = skills_dict
            skill_profile.total_skills_count = len(skills_dict)
            skill_profile.save()
    
    def analyze_resume_for_skills(self, resume_text):
        """Analyze resume text to extract skills based on content patterns"""
        if not resume_text:
            return {}
        
        text_lower = resume_text.lower()
        skills_dict = {}
        
        # Programming languages and technologies
        programming_keywords = {
            'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'tensorflow', 'pytorch'],
            'javascript': ['javascript', 'react', 'node', 'express', 'vue', 'angular', 'typescript'],
            'java': ['java', 'spring', 'hibernate', 'maven', 'junit'],
            'c++': ['c++', 'cpp', 'stl', 'boost'],
            'c#': ['c#', '.net', 'asp.net', 'entity framework'],
            'php': ['php', 'laravel', 'wordpress', 'composer'],
            'ruby': ['ruby', 'rails', 'sinatra'],
            'go': ['go', 'golang', 'gorilla'],
            'rust': ['rust', 'cargo', 'tokio'],
            'swift': ['swift', 'ios', 'xcode'],
            'kotlin': ['kotlin', 'android', 'jetpack compose'],
        }
        
        # Web technologies
        web_keywords = {
            'html': ['html', 'html5', 'css', 'css3', 'bootstrap', 'tailwind'],
            'react': ['react', 'redux', 'hooks', 'jsx'],
            'angular': ['angular', 'typescript', 'rxjs'],
            'vue': ['vue', 'vuex', 'nuxt'],
            'node.js': ['node', 'express', 'npm', 'yarn'],
        }
        
        # Databases
        database_keywords = {
            'sql': ['sql', 'mysql', 'postgresql', 'oracle', 'sql server'],
            'nosql': ['mongodb', 'redis', 'cassandra', 'dynamodb'],
            'postgresql': ['postgresql', 'postgres', 'psql'],
            'mysql': ['mysql', 'mariadb'],
        }
        
        # Cloud and DevOps
        cloud_keywords = {
            'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'rds'],
            'azure': ['azure', 'microsoft azure', 'azure functions', 'blob storage'],
            'gcp': ['google cloud', 'gcp', 'google cloud platform'],
            'docker': ['docker', 'containers', 'kubernetes', 'k8s'],
            'jenkins': ['jenkins', 'ci/cd', 'continuous integration'],
            'git': ['git', 'github', 'gitlab', 'bitbucket', 'version control'],
        }
        
        # Engineering disciplines
        engineering_keywords = {
            'autocad': ['autocad', 'cad', 'solidworks', 'revit'],
            'matlab': ['matlab', 'simulink'],
            'labview': ['labview', 'ni'],
            'staad': ['staad.pro', 'structural analysis'],
            'ansys': ['ansys', 'finite element analysis'],
            'cfd': ['cfd', 'computational fluid dynamics'],
        }
        
        # Combine all keyword sets
        all_keywords = {
            **programming_keywords,
            **web_keywords,
            **database_keywords,
            **cloud_keywords,
            **engineering_keywords
        }
        
        # Find matching skills
        for skill, keywords in all_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    skills_dict[skill] = 'intermediate'
                    break
        
        return skills_dict


class SkillProfile(models.Model):
    """Skill profile for tracking user's skills and proficiency"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='skill_profile')
    skills = models.JSONField(default=dict, blank=True)  # {skill_name: proficiency_level}
    total_skills_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Skill Profile - {self.user.email}"


class ResumeAnalysis(models.Model):
    """Store detailed analysis results for each resume"""
    
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='analysis')
    
    # Analysis metrics
    completeness_score = models.FloatField(default=0.0)  # 0-100
    skills_score = models.FloatField(default=0.0)  # 0-100
    experience_score = models.FloatField(default=0.0)  # 0-100
    education_score = models.FloatField(default=0.0)  # 0-100
    overall_score = models.FloatField(default=0.0)  # 0-100
    
    # New detailed score components
    projects_score = models.FloatField(default=0.0)  # 0-100
    structure_score = models.FloatField(default=0.0)  # 0-100
    certification_score = models.FloatField(default=0.0)  # 0-100
    achievement_score = models.FloatField(default=0.0)  # 0-100
    
    # Recommendations
    missing_skills = models.JSONField(default=list, blank=True)
    improvement_suggestions = models.JSONField(default=list, blank=True)
    skill_gaps = models.JSONField(default=dict, blank=True)
    
    # Analysis details
    word_count = models.IntegerField(default=0)
    sentence_count = models.IntegerField(default=0)
    readability_score = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Analysis for {self.resume.title}"
