"""
Enhanced scraping utilities for better contact extraction
"""

import re
from typing import List, Dict, Set, Tuple
from bs4 import BeautifulSoup, Tag


class ContactExtractor:
    """Enhanced contact information extraction"""
    
    # Common job titles to look for
    TARGET_TITLES = [
        # Government/Education
        'director', 'coordinator', 'manager', 'administrator', 'chief',
        'supervisor', 'officer', 'specialist', 'head', 'chair',
        # Specific roles
        'activities director', 'program director', 'training manager',
        'development director', 'hr director', 'compliance officer',
        'education coordinator', 'adult services', 'continuing education',
        # Senior roles
        'executive director', 'assistant director', 'associate director',
        'deputy director', 'regional director', 'vice president',
    ]
    
    # Email patterns to exclude (spam/invalid)
    EMAIL_BLACKLIST = [
        'example.com', 'domain.com', 'email.com', 'test.com',
        'yourcompany.com', 'company.com', 'yourdomain.com',
        'sample.com', 'placeholder.com', 'noreply', 'no-reply',
        'donotreply', 'mailer-daemon', 'postmaster'
    ]
    
    def __init__(self):
        self.name_pattern = re.compile(
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        )
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
    def extract_emails(self, text: str, soup: BeautifulSoup = None) -> List[str]:
        """
        Extract emails from text and HTML
        """
        emails = set()
        
        # Extract from plain text
        text_emails = self.email_pattern.findall(text)
        emails.update(text_emails)
        
        # Extract from mailto links if soup provided
        if soup:
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
            for link in mailto_links:
                href = link.get('href', '')
                email = href.replace('mailto:', '').split('?')[0].strip()
                if '@' in email:
                    emails.add(email)
        
        # Filter out blacklisted emails
        valid_emails = [
            e for e in emails 
            if not any(blocked in e.lower() for blocked in self.EMAIL_BLACKLIST)
            and len(e) > 5  # Minimum reasonable length
        ]
        
        return sorted(list(set(valid_emails)))
    
    def extract_names_with_titles(self, text: str, soup: BeautifulSoup = None) -> List[Dict[str, str]]:
        """
        Extract names along with their associated titles/roles
        Returns list of dicts: {'name': 'John Doe', 'title': 'Director'}
        """
        contacts = []
        
        # Strategy 1: Look for structured contact lists
        if soup:
            contacts.extend(self._extract_from_structured_html(soup))
        
        # Strategy 2: Pattern matching in text
        contacts.extend(self._extract_from_text_patterns(text))
        
        # Deduplicate
        unique_contacts = {}
        for contact in contacts:
            key = contact['name'].lower()
            if key not in unique_contacts:
                unique_contacts[key] = contact
        
        return list(unique_contacts.values())
    
    def _extract_from_structured_html(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract from structured HTML like staff directories
        """
        contacts = []
        
        # Look for common staff directory structures
        # Pattern 1: div/section with class containing 'staff', 'team', 'directory'
        staff_containers = soup.find_all(['div', 'section', 'article'], 
            class_=re.compile(r'(staff|team|directory|person|member|contact)', re.I))
        
        for container in staff_containers:
            name = None
            title = None
            
            # Look for name in heading or strong tags
            name_tags = container.find_all(['h2', 'h3', 'h4', 'strong', 'b'], limit=3)
            for tag in name_tags:
                text = tag.get_text().strip()
                if self._looks_like_name(text):
                    name = text
                    break
            
            # Look for title near the name
            if name:
                # Check siblings and nearby elements
                parent = container
                for elem in parent.find_all(['p', 'span', 'div'], limit=5):
                    text = elem.get_text().strip().lower()
                    if any(title_word in text for title_word in self.TARGET_TITLES):
                        title = elem.get_text().strip()
                        break
            
            if name and title:
                contacts.append({'name': name, 'title': title})
        
        return contacts
    
    def _extract_from_text_patterns(self, text: str) -> List[Dict[str, str]]:
        """
        Extract names and titles using pattern matching
        """
        contacts = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: "Title: Name" or "Title - Name"
            for title in self.TARGET_TITLES:
                pattern = rf'(?i){re.escape(title)}[:\-\s]+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
                match = re.search(pattern, line)
                if match:
                    contacts.append({
                        'name': match.group(1).strip(),
                        'title': title.title()
                    })
            
            # Pattern 2: "Name, Title" or "Name - Title"
            name_title_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)[,\-]\s*(.+)'
            match = re.search(name_title_pattern, line)
            if match:
                name, potential_title = match.groups()
                if any(title_word in potential_title.lower() for title_word in self.TARGET_TITLES):
                    contacts.append({
                        'name': name.strip(),
                        'title': potential_title.strip()
                    })
            
            # Pattern 3: Name on one line, title on next line
            if i < len(lines) - 1 and self._looks_like_name(line):
                next_line = lines[i + 1].strip().lower()
                if any(title in next_line for title in self.TARGET_TITLES):
                    contacts.append({
                        'name': line,
                        'title': lines[i + 1].strip()
                    })
        
        return contacts
    
    def _looks_like_name(self, text: str) -> bool:
        """
        Check if text looks like a person's name
        """
        # Basic heuristics
        if len(text) < 4 or len(text) > 50:
            return False
        
        # Should be 2-4 words
        words = text.split()
        if len(words) < 2 or len(words) > 4:
            return False
        
        # Each word should be capitalized
        if not all(w[0].isupper() for w in words if w):
            return False
        
        # Shouldn't contain job title words
        text_lower = text.lower()
        if any(title in text_lower for title in ['director', 'manager', 'coordinator', 'chief']):
            return False
        
        return True
    
    def find_contact_pages(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Find links to contact, staff, or about pages
        """
        contact_keywords = [
            'contact', 'staff', 'team', 'directory', 'about',
            'leadership', 'people', 'faculty', 'administration',
            'our team', 'meet the', 'who we are'
        ]
        
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            
            if any(keyword in href or keyword in text for keyword in contact_keywords):
                # Make absolute URL
                from urllib.parse import urljoin
                full_url = urljoin(base_url, link['href'])
                links.append(full_url)
        
        return list(set(links))[:10]  # Limit to top 10


class SearchQueryBuilder:
    """Build effective search queries for different entity types"""
    
    @staticmethod
    def build_department_query(county: str, state: str, department: str) -> str:
        """Build query for government departments"""
        # Add common variations
        variations = {
            'IT Training': ['IT training', 'information technology training', 'computer training'],
            'Cybersecurity': ['cybersecurity', 'cyber security', 'information security'],
            'Department of Aging': ['aging services', 'senior services', 'office on aging', 'area agency on aging'],
            'Workforce Services': ['workforce development', 'employment services', 'job services'],
            'Public Schools Staff Development': ['professional development', 'teacher training', 'staff development'],
            'Community College Continuing Education': ['continuing education', 'workforce development', 'adult education'],
            'Public Library': ['public library', 'library system', 'county library']
        }
        
        terms = variations.get(department, [department.lower()])
        # Use the first variation for the main query
        return f'"{county}" {state} {terms[0]} site:.gov'
    
    @staticmethod
    def build_retirement_query(county: str, state: str) -> str:
        """Build query for retirement communities"""
        return f'"{county}" {state} (retirement community OR assisted living OR senior living)'
    
    @staticmethod
    def build_hospital_query(county: str, state: str) -> str:
        """Build query for hospitals and healthcare"""
        return f'"{county}" {state} (hospital OR medical center OR healthcare system)'
    
    @staticmethod
    def build_chamber_query(county: str, state: str) -> str:
        """Build query for business associations"""
        return f'"{county}" {state} (chamber of commerce OR business association)'


class DataValidator:
    """Validate and clean extracted data"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format and content"""
        if not email or '@' not in email:
            return False
        
        # Check format
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Check for common invalid patterns
        invalid_patterns = ['noreply', 'no-reply', 'donotreply', 'example', 'test', 'spam']
        email_lower = email.lower()
        if any(pattern in email_lower for pattern in invalid_patterns):
            return False
        
        return True
    
    @staticmethod
    def clean_phone(phone: str) -> str:
        """Clean and format phone number"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Format as (XXX) XXX-XXXX if we have 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return phone  # Return original if can't format
    
    @staticmethod
    def deduplicate_contacts(contacts: List[Dict]) -> List[Dict]:
        """Remove duplicate contacts based on name similarity"""
        unique = {}
        
        for contact in contacts:
            # Normalize name for comparison
            name_key = contact['name'].lower().strip()
            name_key = re.sub(r'\s+', ' ', name_key)  # Normalize whitespace
            
            if name_key not in unique:
                unique[name_key] = contact
        
        return list(unique.values())
