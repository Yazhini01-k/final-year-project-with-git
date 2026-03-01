import os
import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Resume, SkillProfile, ResumeAnalysis
from .serializers import (
    ResumeSerializer, ResumeCreateSerializer, ResumeDetailSerializer,
    SkillProfileSerializer, ResumeAnalysisSerializer
)
from .utils import ResumeTextExtractor, ResumeParser, FeatureVectorizer
from accounts.models import User


class ResumeUploadView(generics.CreateAPIView):
    """Upload and process resume"""
    serializer_class = ResumeCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        # Save the resume file
        resume = serializer.save(user=self.request.user)
        
        # Start async processing (in production, use Celery)
        try:
            self._process_resume(resume)
        except Exception as e:
            resume.processing_status = 'failed'
            resume.error_message = str(e)
            resume.save()
    
    def _process_resume(self, resume):
        """Process uploaded resume"""
        # Update status
        resume.processing_status = 'processing'
        resume.save()
        
        # Extract file extension
        file_extension = resume.file.name.split('.')[-1].lower()
        resume.file_type = file_extension
        resume.file_size = resume.file.size
        resume.original_filename = resume.file.name.split('/')[-1]
        
        # Extract text
        extractor = ResumeTextExtractor()
        file_path = resume.file.path
        raw_text = extractor.extract_text(file_path, file_extension)
        resume.raw_text = raw_text
        
        # Parse resume content
        parser = ResumeParser()
        parsed_data = parser.parse_resume(raw_text)
        
        # Update resume with parsed data
        resume.processed_text = parsed_data['processed_text']
        resume.extracted_skills = parsed_data['extracted_skills']
        resume.extracted_education = parsed_data['extracted_education']
        resume.extracted_experience = parsed_data['extracted_experience']
        resume.extracted_contact_info = parsed_data['extracted_contact_info']
        
        # NEW: Store additional extracted data
        resume.extracted_projects = parsed_data['extracted_projects']
        resume.extracted_certificates = parsed_data['extracted_certificates']
        resume.extracted_achievements = parsed_data['extracted_achievements']
        
        # Create feature vector
        vectorizer = FeatureVectorizer(max_features=settings.TF_IDF_MAX_FEATURES)
        try:
            # Get all processed resumes for fitting
            all_resumes = Resume.objects.filter(
                processing_status='completed'
            ).exclude(id=resume.id)
            
            if all_resumes.exists():
                # Fit on existing resumes and transform new one
                documents = [r.processed_text for r in all_resumes if r.processed_text]
                documents.append(resume.processed_text)
                vectors = vectorizer.fit_transform(documents)
                resume.feature_vector = vectors[-1]  # Get last vector (new resume)
                resume.skill_keywords = vectorizer.get_feature_names()
            else:
                # First resume, fit on just this one
                vectors = vectorizer.fit_transform([resume.processed_text])
                resume.feature_vector = vectors[0]
                resume.skill_keywords = vectorizer.get_feature_names()
                
        except Exception as e:
            # If vectorization fails, continue without it
            resume.feature_vector = []
            resume.skill_keywords = []
        
        # Update processing status
        resume.processing_status = 'completed'
        resume.save()
        
        # Update user's skill profile using STRICT method
        self._create_strict_skill_profile(resume.user, resume.extracted_skills)
        
        # Create analysis
        self._create_resume_analysis(resume)
    
    def _create_strict_skill_profile(self, user, skills):
        """STRICT: Create or update user's skill profile based ONLY on extracted skills"""
        if not skills:
            return
        
        # Create skills dictionary ONLY from extracted skills
        skills_dict = {}
        for skill in skills:
            if isinstance(skill, str) and skill.strip():
                skills_dict[skill.lower().strip()] = 'intermediate'
        
        if not skills_dict:
            return
        
        # Get or create skill profile
        skill_profile, created = SkillProfile.objects.get_or_create(
            user=user,
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
    
    def _create_resume_analysis(self, resume):
        """Create resume analysis"""
        analysis = ResumeAnalysis.objects.create(resume=resume)
        
        # Calculate scores (simplified version)
        text = resume.raw_text or ""
        
        # Word count
        words = text.split()
        analysis.word_count = len(words)
        
        # Sentence count
        import nltk
        try:
            analysis.sentence_count = len(nltk.sent_tokenize(text))
        except:
            analysis.sentence_count = text.count('.') + text.count('!') + text.count('?')
        
        # Calculate individual scores (0-100)
        skills_score = self._calculate_skills_score(resume)
        projects_score = self._calculate_projects_score(resume)
        education_score = self._calculate_education_score(resume)
        structure_score = self._calculate_structure_score(resume)
        cert_score = self._calculate_certification_score(resume)
        achievement_score = self._calculate_achievement_score(resume)
        
        # Check for existence of experience
        experience_list = resume.extracted_experience or []
        has_experience = len(experience_list) > 0
        
        # Dynamic weighted scoring based on experience presence
        if has_experience:
            # Case: Experience exists (Experience 15%, Skills 60%)
            experience_score = self._calculate_experience_score(resume)
            total_score = (
                (skills_score * 0.60) +      # Skills
                (experience_score * 0.15) +  # Experience
                (projects_score * 0.10) +    # Projects
                (education_score * 0.10) +   # Education
                (cert_score * 0.03) +       # Certifications
                (structure_score * 0.01) +  # Structure
                (achievement_score * 0.01)   # Achievements
            )
        else:
            # Case: Experience does NOT exist (Skills weight increased to 75%)
            experience_score = 0  # No experience score
            total_score = (
                (skills_score * 0.75) +      # Skills (increased weight)
                (projects_score * 0.10) +    # Projects
                (education_score * 0.10) +   # Education
                (cert_score * 0.03) +       # Certifications
                (structure_score * 0.01) +  # Structure
                (achievement_score * 0.01)   # Achievements
            )
        
        # Store individual scores
        analysis.skills_score = skills_score
        analysis.experience_score = experience_score
        analysis.education_score = education_score
        
        # Store new score components
        analysis.projects_score = projects_score
        analysis.structure_score = structure_score
        analysis.certification_score = cert_score
        analysis.achievement_score = achievement_score
        
        # Store overall score
        analysis.overall_score = round(total_score, 2)
        
        # Store completeness for backward compatibility
        analysis.completeness_score = self._calculate_completeness_score(resume)
        
        analysis.save()

    def _calculate_skills_score(self, resume):
        """Calculate skills score based on number and quality of skills"""
        skills_count = len(resume.extracted_skills) if resume.extracted_skills else 0
        # Base score: 5 points per skill, max 100
        base_score = min(100, skills_count * 5)
        
        # Bonus for diverse skill categories
        if skills_count >= 10:
            return min(100, base_score + 10)
        elif skills_count >= 5:
            return min(100, base_score + 5)
        return base_score
    
    def _calculate_experience_score(self, resume):
        """Calculate experience score based on work experience"""
        exp_count = len(resume.extracted_experience) if resume.extracted_experience else 0
        # Base score: 20 points per experience entry, max 100
        return min(100, exp_count * 20)
    
    def _calculate_projects_score(self, resume):
        """Calculate projects score from resume text"""
        text = resume.raw_text or ""
        text_lower = text.lower()
        
        project_keywords = [
            'project', 'portfolio', 'developed', 'built', 'created', 'designed',
            'implemented', 'launched', 'deployed', 'application', 'website',
            'software', 'system', 'platform', 'tool', 'app'
        ]
        
        project_count = sum(1 for keyword in project_keywords if keyword in text_lower)
        return min(100, project_count * 10)
    
    def _calculate_education_score(self, resume):
        """Calculate education score based on education entries"""
        edu_count = len(resume.extracted_education) if resume.extracted_education else 0
        # Base score: 25 points per education entry, max 100
        return min(100, edu_count * 25)
    
    def _calculate_structure_score(self, resume):
        """Calculate structure score based on resume organization"""
        text = resume.raw_text or ""
        score = 0
        
        # Check for common resume sections
        sections = ['skills', 'experience', 'education', 'contact', 'summary', 'objective']
        text_lower = text.lower()
        
        for section in sections:
            if section in text_lower:
                score += 15
        
        # Bonus for proper formatting
        if text.count('\n') > 5:  # Has multiple lines
            score += 10
        
        return min(100, score)
    
    def _calculate_certification_score(self, resume):
        """Calculate certification score from resume text"""
        text = resume.raw_text or ""
        text_lower = text.lower()
        
        cert_keywords = [
            'certified', 'certificate', 'certification', 'license', 'accredited',
            'pmp', 'aws certified', 'google certified', 'microsoft certified',
            'cisco', 'comptia', 'iso', 'professional certification'
        ]
        
        cert_count = sum(1 for keyword in cert_keywords if keyword in text_lower)
        return min(100, cert_count * 20)
    
    def _calculate_achievement_score(self, resume):
        """Calculate achievement score from resume text"""
        text = resume.raw_text or ""
        text_lower = text.lower()
        
        achievement_keywords = [
            'achieved', 'awarded', 'recognized', 'honor', 'award', 'trophy',
            'promotion', 'increased', 'improved', 'optimized', 'reduced',
            'saved', 'generated', 'led', 'managed', 'won', 'success'
        ]
        
        achievement_count = sum(1 for keyword in achievement_keywords if keyword in text_lower)
        return min(100, achievement_count * 8)
    
    def _calculate_completeness_score(self, resume):
        """Calculate completeness score for backward compatibility"""
        completeness_score = 0
        if resume.extracted_skills:
            completeness_score += 25
        if resume.extracted_education:
            completeness_score += 25
        if resume.extracted_experience:
            completeness_score += 25
        if resume.extracted_contact_info:
            completeness_score += 25
        return completeness_score


class ResumeListView(generics.ListAPIView):
    """List user's resumes"""
    serializer_class = ResumeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


class ResumeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Resume detail view"""
    serializer_class = ResumeDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


class SkillProfileView(generics.RetrieveUpdateAPIView):
    """User skill profile view"""
    serializer_class = SkillProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = SkillProfile.objects.get_or_create(user=self.request.user)
        return profile


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def resume_analysis(request, resume_id):
    """Get detailed analysis for a specific resume"""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    try:
        analysis = resume.analysis
        serializer = ResumeAnalysisSerializer(analysis)
        return Response(serializer.data)
    except ResumeAnalysis.DoesNotExist:
        return Response(
            {'error': 'Analysis not found for this resume'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reprocess_resume(request, resume_id):
    """Reprocess a resume (useful for debugging or updated parsing logic)"""
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    try:
        # Reset processing status
        resume.processing_status = 'pending'
        resume.error_message = None
        resume.save()
        
        # Reprocess
        upload_view = ResumeUploadView()
        upload_view._process_resume(resume)
        
        return Response({
            'message': 'Resume reprocessed successfully',
            'status': resume.processing_status
        })
    except Exception as e:
        resume.processing_status = 'failed'
        resume.error_message = str(e)
        resume.save()
        return Response(
            {'error': f'Failed to reprocess resume: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
