import os
import json
import re
from io import BytesIO
from PIL import Image
import pdfplumber
import docx
import pytesseract
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer


class ResumeTextExtractor:
    """Extract text from various resume file formats"""
    
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
    
    def extract_text(self, file_path, file_type):
        """Extract text from resume file based on file type"""
        try:
            if file_type.lower() == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type.lower() == 'docx':
                return self._extract_from_docx(file_path)
            elif file_type.lower() in ['jpg', 'jpeg', 'png']:
                return self._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise Exception(f"Error extracting text: {str(e)}")
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
        
        return text.strip() if text else ""
    
    def _extract_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    def _extract_from_image(self, file_path):
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            raise Exception(f"Error performing OCR: {str(e)}")


class ResumeParser:
    """Parse and extract structured information from resume text"""
    
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        
        # Common skill keywords
        self.skill_keywords = [
            'python', 'java', 'javascript', 'react', 'django', 'node.js', 'sql',
            'html', 'css', 'aws', 'docker', 'kubernetes', 'git', 'linux', 'mongodb',
            'postgresql', 'mysql', 'redis', 'elasticsearch', 'tensorflow', 'pytorch',
            'machine learning', 'data science', 'artificial intelligence', 'deep learning',
            'nlp', 'computer vision', 'api', 'rest', 'graphql', 'microservices',
            'agile', 'scrum', 'devops', 'ci/cd', 'testing', 'unit testing',
            'integration testing', 'ui', 'ux', 'frontend', 'backend', 'full stack'
        ]
        
        # Education keywords
        self.education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'university',
            'college', 'institute', 'engineering', 'computer science', 'information technology',
            'business administration', 'mba', 'b.tech', 'm.tech', 'b.sc', 'm.sc'
        ]
    
    def parse_resume(self, text):
        """Parse resume text and extract structured information"""
        processed_text = self._preprocess_text(text)
        
        return {
            'processed_text': processed_text,
            'extracted_skills': self._extract_skills(text, processed_text),
            'extracted_education': self._extract_education(text),
            'extracted_experience': self._extract_experience(text),
            'extracted_contact_info': self._extract_contact_info(text),
            # NEW: Additional extractions
            'extracted_projects': self._extract_projects(text),
            'extracted_certificates': self._extract_certificates(text),
            'extracted_achievements': self._extract_achievements(text)
        }
    
    def _preprocess_text(self, text):
        """Preprocess text for NLP analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\-@.,]', ' ', text)
        
        # Tokenize and remove stopwords
        tokens = word_tokenize(text)
        tokens = [token for token in tokens if token not in stopwords.words('english')]
        
        # Lemmatize
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(token) for token in tokens]
        
        return ' '.join(tokens)
    
    def _extract_skills(self, original_text, processed_text):
        """Extract skills from resume text"""
        skills = set()
        text_lower = original_text.lower()
        
        # Check for skill keywords
        for skill in self.skill_keywords:
            if skill in text_lower:
                skills.add(skill)
        
        # Use NLP to extract technical terms
        doc = self.nlp(original_text)
        
        # Extract named entities that might be skills
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT']:
                ent_text = ent.text.lower()
                if any(keyword in ent_text for keyword in ['python', 'java', 'javascript', 'sql']):
                    skills.add(ent.text)
        
        # Extract noun chunks that might be skills
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            if any(keyword in chunk_text for keyword in self.skill_keywords):
                skills.add(chunk.text)
        
        return list(skills)
    
    def _extract_education(self, text):
        """Extract education information"""
        education = []
        text_lower = text.lower()
        
        # Look for education patterns
        education_patterns = [
            r'(bachelor|master|phd|doctorate|b\.tech|m\.tech|b\.sc|m\.sc|mba|b\.e).*?(\d{4})',
            r'(university|college|institute).*?(bachelor|master|phd|degree)',
            r'(engineering|computer science|information technology).*?(degree|bachelor|master)'
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    education.append(' '.join(match))
                else:
                    education.append(match)
        
        return list(set(education))
    
    def _extract_experience(self, text):
        """Extract work experience information"""
        experience = []
        
        # Look for experience patterns
        experience_patterns = [
            r'(\d+).*?years?.*?experience',
            r'(\w+\s+\w{2,}\s+\w+).*?(\d{4}\s*-\s*\d{4}|\d{4}\s*-\s*present)',
            r'(senior|junior|lead|principal|manager).*?(developer|engineer|analyst|designer)'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    experience.append(' '.join(match))
                else:
                    experience.append(match)
        
        return list(set(experience))
    
    def _extract_projects(self, text):
        """Extract project information from resume"""
        projects = []
        text_lower = text.lower()
        
        # Project section patterns
        project_section_patterns = [
            r'projects[:\s]*(.*?)(?:experience|education|skills|$)',
            r'personal projects[:\s]*(.*?)(?:experience|education|skills|$)',
            r'academic projects[:\s]*(.*?)(?:experience|education|skills|$)'
        ]
        
        # Extract project sections
        for pattern in project_section_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                projects.append(match.strip())
        
        # Individual project patterns
        project_patterns = [
            r'[-•*]\s*([^.!?]*?[a-zA-Z][^.!?]*?(?:project|app|system|platform|tool|application)[^.!?]*)',
            r'([^.!?]*?(?:developed|built|created|designed|implemented|launched)[^.!?]*?[a-zA-Z][^.!?]*)',
            r'([^.!?]*?(?:website|web app|mobile app|software|database)[^.!?]*?[a-zA-Z][^.!?]*)'
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:  # Filter out very short matches
                    projects.append(match.strip())
        
        return list(set(projects))
    
    def _extract_certificates(self, text):
        """Extract certificate information from resume"""
        certificates = []
        text_lower = text.lower()
        
        # Certificate patterns
        cert_patterns = [
            r'(certified\s+[^.!?]*?[a-zA-Z][^.!?]*)',
            r'([^.!?]*?certificate[s]?[^.!?]*?[a-zA-Z][^.!?]*)',
            r'([^.!?]*?certification[s]?[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(aws certified[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(google certified[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(microsoft certified[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(pmp[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(cisco[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(comptia[^.!?]*?[a-zA-Z][^.!?]*)',
            r'(iso[^.!?]*?[a-zA-Z][^.!?]*)'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 5:  # Filter out very short matches
                    certificates.append(match.strip())
        
        return list(set(certificates))
    
    def _extract_achievements(self, text):
        """Extract achievement information from resume"""
        achievements = []
        text_lower = text.lower()
        
        # Achievement patterns
        achievement_patterns = [
            r'[-•*]\s*([^.!?]*?(?:achieved|awarded|recognized|honor|award|trophy)[^.!?]*?[a-zA-Z][^.!?]*)',
            r'[-•*]\s*([^.!?]*?(?:promotion|increased|improved|optimized|reduced)[^.!?]*?[a-zA-Z][^.!?]*)',
            r'[-•*]\s*([^.!?]*?(?:saved|generated|led|managed|won|success)[^.!?]*?[a-zA-Z][^.!?]*)',
            r'([^.!?]*?\d+%[^.!?]*?(?:increase|decrease|improvement|reduction)[^.!?]*)',
            r'([^.!?]*?\$?\d+(?:,\d{3})*(?:\.\d{2})?[^.!?]*?(?:saved|generated|revenue|profit|cost)[^.!?]*)',
            r'([^.!?]*?(?:first|top|best|excellent|outstanding)[^.!?]*?[a-zA-Z][^.!?]*)'
        ]
        
        for pattern in achievement_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 8:  # Filter out very short matches
                    achievements.append(match.strip())
        
        return list(set(achievements))
    
    def _extract_contact_info(self, text):
        """Extract contact information"""
        contact_info = {}
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Phone
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = phones[0]
        
        # LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_matches:
            contact_info['linkedin'] = 'https://' + linkedin_matches[0]
        
        return contact_info


class FeatureVectorizer:
    """Convert resume text to feature vectors using TF-IDF"""
    
    def __init__(self, max_features=5000):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=1.0
        )
        self.is_fitted = False
    
    def fit_transform(self, documents):
        """Fit vectorizer and transform documents"""
        vectors = self.vectorizer.fit_transform(documents)
        self.is_fitted = True
        return vectors.toarray().tolist()
    
    def transform(self, documents):
        """Transform documents using fitted vectorizer"""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted before transforming")
        vectors = self.vectorizer.transform(documents)
        return vectors.toarray().tolist()
    
    def get_feature_names(self):
        """Get feature names (vocabulary)"""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted first")
        return self.vectorizer.get_feature_names_out().tolist()
