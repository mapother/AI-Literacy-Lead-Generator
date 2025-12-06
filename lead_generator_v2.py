"""
Lead Generator v2.0 - Pragmatic Approach
No search dependency - uses direct URLs and intelligent scraping
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from typing import List, Dict, Optional, Tuple
import logging
from urllib.parse import urljoin, urlparse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lead_generator_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ContactExtractor:
    """Extract emails and contacts from HTML"""
    
    def __init__(self):
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.email_blacklist = [
            'example.com', 'domain.com', 'test.com', 'noreply',
            'no-reply', 'donotreply', 'mailer-daemon'
        ]
        
    def extract_emails(self, text: str, soup: BeautifulSoup = None) -> List[str]:
        """Extract valid email addresses"""
        emails = set()
        
        # From text
        text_emails = self.email_pattern.findall(text)
        emails.update(text_emails)
        
        # From mailto links
        if soup:
            for link in soup.find_all('a', href=re.compile(r'^mailto:', re.I)):
                href = link.get('href', '')
                email = href.replace('mailto:', '').split('?')[0].strip()
                if '@' in email:
                    emails.add(email)
        
        # Filter blacklist
        valid = [e for e in emails if not any(b in e.lower() for b in self.email_blacklist)]
        return sorted(list(set(valid)))
    
    def extract_contact_info(self, soup: BeautifulSoup) -> Dict:
        """Extract names, titles, and emails from structured content"""
        contacts = []
        
        # Look for staff/team sections
        staff_sections = soup.find_all(['div', 'section', 'article'], 
            class_=re.compile(r'(staff|team|directory|contact|about)', re.I))
        
        for section in staff_sections:
            # Try to find name-title-email groups
            text = section.get_text()
            
            # Pattern: Name followed by title
            name_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            title_pattern = r'(Director|Coordinator|Manager|Administrator|Chief|Officer|Supervisor)'
            
            combined_pattern = rf'{name_pattern}[,\s]+{title_pattern}'
            matches = re.findall(combined_pattern, text)
            
            for match in matches:
                if len(match) >= 2:
                    contacts.append({
                        'name': match[0].strip(),
                        'title': match[1].strip() if len(match) > 1 else ''
                    })
        
        return {
            'contacts': contacts[:10],  # Limit to top 10
            'emails': self.extract_emails(soup.get_text(), soup)
        }


class CountyURLBuilder:
    """Build direct URLs for county websites"""
    
    @staticmethod
    def get_county_patterns(county_name: str, state: str) -> List[str]:
        """Generate likely URL patterns for county websites"""
        # Clean county name
        clean_name = county_name.lower().replace(' county', '').replace(' ', '')
        state_lower = state.lower()
        
        patterns = [
            f"https://{clean_name}countymd.gov" if state == 'MD' else None,
            f"https://{clean_name}county{state_lower}.gov",
            f"https://www.{clean_name}county{state_lower}.gov",
            f"https://{clean_name}{state_lower}.gov",
            f"https://www.{clean_name}{state_lower}.gov",
            f"https://www.co.{clean_name}.{state_lower}.us",
            f"https://co.{clean_name}.{state_lower}.us",
        ]
        
        return [p for p in patterns if p]
    
    @staticmethod
    def get_department_patterns(base_url: str, dept_type: str) -> List[str]:
        """Generate likely URLs for department pages"""
        dept_slugs = {
            'aging': ['aging', 'seniors', 'senior-services', 'office-on-aging'],
            'it': ['it', 'technology', 'information-technology'],
            'cybersecurity': ['cybersecurity', 'security', 'information-security'],
            'workforce': ['workforce', 'employment', 'jobs', 'career-services'],
            'schools': ['schools', 'education', 'public-schools'],
            'library': ['library', 'libraries'],
            'community-college': ['community-college', 'continuing-ed', 'workforce-development']
        }
        
        base = base_url.rstrip('/')
        patterns = []
        
        for slug in dept_slugs.get(dept_type, [dept_type]):
            patterns.extend([
                f"{base}/departments/{slug}",
                f"{base}/{slug}",
                f"{base}/services/{slug}",
                f"{base}/residents/{slug}",
            ])
        
        return patterns


class PragmaticLeadGenerator:
    """Lead generator that doesn't rely on search engines"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.delay = 2
        self.contact_extractor = ContactExtractor()
        self.url_builder = CountyURLBuilder()
        self.results = []
        
    def test_url(self, url: str) -> Optional[BeautifulSoup]:
        """Test if a URL exists and return soup if successful"""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.debug(f"URL failed {url}: {e}")
        return None
    
    def find_county_website(self, county_name: str, state: str) -> Tuple[Optional[str], Optional[BeautifulSoup]]:
        """Find county website by trying common patterns"""
        logger.info(f"Looking for {county_name}, {state} website...")
        
        patterns = self.url_builder.get_county_patterns(county_name, state)
        
        for url in patterns:
            soup = self.test_url(url)
            if soup:
                logger.info(f"  ✓ Found: {url}")
                time.sleep(self.delay)
                return url, soup
        
        logger.warning(f"  ✗ Could not find website for {county_name}, {state}")
        return None, None
    
    def find_contact_pages(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find contact/about/staff pages on a website"""
        keywords = ['contact', 'about', 'staff', 'directory', 'team', 'departments']
        pages = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().lower()
            
            if any(kw in href or kw in text for kw in keywords):
                full_url = urljoin(base_url, link['href'])
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    pages.append(full_url)
        
        return list(set(pages))[:10]
    
    def scrape_for_departments(self, county_url: str, soup: BeautifulSoup) -> Dict:
        """Look for department information on county website"""
        departments = {}
        
        dept_types = {
            'aging': 'Department of Aging',
            'it': 'IT Training',
            'cybersecurity': 'Cybersecurity',
            'workforce': 'Workforce Services',
            'schools': 'Public Schools',
            'library': 'Public Library'
        }
        
        # Try direct department URLs
        for dept_key, dept_name in dept_types.items():
            logger.info(f"  Looking for {dept_name}...")
            
            patterns = self.url_builder.get_department_patterns(county_url, dept_key)
            found = False
            
            for pattern in patterns:
                dept_soup = self.test_url(pattern)
                if dept_soup:
                    contact_info = self.contact_extractor.extract_contact_info(dept_soup)
                    departments[dept_name] = {
                        'found': True,
                        'url': pattern,
                        'emails': contact_info['emails'],
                        'contacts': contact_info['contacts']
                    }
                    logger.info(f"    ✓ Found at {pattern}")
                    found = True
                    time.sleep(self.delay)
                    break
            
            if not found:
                # Look for department links in main page
                for link in soup.find_all('a', href=True):
                    link_text = link.get_text().lower()
                    if dept_key in link_text or dept_name.lower() in link_text:
                        dept_url = urljoin(county_url, link['href'])
                        dept_soup = self.test_url(dept_url)
                        if dept_soup:
                            contact_info = self.contact_extractor.extract_contact_info(dept_soup)
                            departments[dept_name] = {
                                'found': True,
                                'url': dept_url,
                                'emails': contact_info['emails'],
                                'contacts': contact_info['contacts']
                            }
                            logger.info(f"    ✓ Found via link: {dept_url}")
                            found = True
                            time.sleep(self.delay)
                            break
            
            if not found:
                departments[dept_name] = {
                    'found': False,
                    'url': None,
                    'emails': [],
                    'contacts': []
                }
                logger.info(f"    ✗ Not found")
        
        return departments
    
    def find_organizations(self, county_name: str, state: str, org_type: str) -> List[Dict]:
        """
        Find organizations - this will create a manual research list
        since we can't search
        """
        # For now, return empty and add to manual research list
        logger.info(f"  {org_type}: Needs manual research")
        return []
    
    def process_county(self, county: Dict) -> Dict:
        """Process a single county"""
        county_name = county['name']
        state = county['state']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {county_name}, {state}")
        logger.info(f"{'='*60}")
        
        county_data = {
            'county_name': f"{county_name}, {state}",
            'distance': county['distance'],
            'county_website': None,
            'departments': {},
            'manual_research_needed': []
        }
        
        # Find county website
        county_url, soup = self.find_county_website(county_name, state)
        
        if not county_url:
            county_data['manual_research_needed'].append({
                'type': 'County Website',
                'reason': 'Could not find official .gov website',
                'suggestion': f'Google: "{county_name} {state} official government"'
            })
            return county_data
        
        county_data['county_website'] = county_url
        
        # Extract general contact info from main page
        main_contact = self.contact_extractor.extract_contact_info(soup)
        county_data['general_emails'] = main_contact['emails']
        
        # Find departments
        county_data['departments'] = self.scrape_for_departments(county_url, soup)
        
        # Add manual research items for non-government entities
        county_data['manual_research_needed'].extend([
            {
                'type': 'Retirement Communities',
                'reason': 'Requires search',
                'suggestion': f'Google: "{county_name} {state} retirement community assisted living"'
            },
            {
                'type': 'Hospitals',
                'reason': 'Requires search',
                'suggestion': f'Google: "{county_name} {state} hospital medical center"'
            },
            {
                'type': 'Chamber of Commerce',
                'reason': 'Requires search',
                'suggestion': f'Google: "{county_name} {state} chamber of commerce"'
            }
        ])
        
        return county_data
    
    def get_counties_near_frederick(self, radius_miles: int = 200) -> List[Dict]:
        """Get counties within radius"""
        counties = [
            # Maryland
            {"name": "Frederick County", "state": "MD", "distance": 0},
            {"name": "Montgomery County", "state": "MD", "distance": 30},
            {"name": "Carroll County", "state": "MD", "distance": 25},
            {"name": "Howard County", "state": "MD", "distance": 35},
            {"name": "Washington County", "state": "MD", "distance": 25},
            {"name": "Baltimore County", "state": "MD", "distance": 50},
            {"name": "Anne Arundel County", "state": "MD", "distance": 55},
            {"name": "Prince George's County", "state": "MD", "distance": 45},
            {"name": "Harford County", "state": "MD", "distance": 70},
            {"name": "Charles County", "state": "MD", "distance": 60},
            
            # Virginia
            {"name": "Loudoun County", "state": "VA", "distance": 35},
            {"name": "Fairfax County", "state": "VA", "distance": 45},
            {"name": "Clarke County", "state": "VA", "distance": 30},
            {"name": "Fauquier County", "state": "VA", "distance": 50},
            {"name": "Warren County", "state": "VA", "distance": 45},
            {"name": "Shenandoah County", "state": "VA", "distance": 60},
            {"name": "Prince William County", "state": "VA", "distance": 55},
            {"name": "Arlington County", "state": "VA", "distance": 50},
            {"name": "Alexandria City", "state": "VA", "distance": 55},
            
            # Pennsylvania
            {"name": "Adams County", "state": "PA", "distance": 35},
            {"name": "York County", "state": "PA", "distance": 50},
            {"name": "Franklin County", "state": "PA", "distance": 40},
            {"name": "Cumberland County", "state": "PA", "distance": 60},
            {"name": "Lancaster County", "state": "PA", "distance": 80},
            
            # West Virginia
            {"name": "Berkeley County", "state": "WV", "distance": 45},
            {"name": "Jefferson County", "state": "WV", "distance": 35},
            {"name": "Morgan County", "state": "WV", "distance": 50},
        ]
        
        return [c for c in counties if c["distance"] <= radius_miles]
    
    def export_to_excel(self, data: List[Dict], filename: str = 'lead_results_v2.xlsx'):
        """Export to Excel with separate sheets"""
        logger.info(f"Exporting to {filename}...")
        
        # Main results
        main_rows = []
        manual_rows = []
        
        for county_data in data:
            county_name = county_data['county_name']
            
            # County row
            main_rows.append({
                'County': county_name,
                'Distance': county_data['distance'],
                'Website': county_data.get('county_website', 'NOT FOUND'),
                'General Emails': '; '.join(county_data.get('general_emails', [])),
                'Status': 'Found' if county_data.get('county_website') else 'NEEDS RESEARCH'
            })
            
            # Department rows
            for dept_name, dept_data in county_data.get('departments', {}).items():
                if dept_data['found']:
                    main_rows.append({
                        'County': county_name,
                        'Distance': '',
                        'Website': dept_data.get('url', ''),
                        'General Emails': '; '.join(dept_data.get('emails', [])),
                        'Status': f"FOUND: {dept_name}"
                    })
                    
                    # Add contacts
                    for contact in dept_data.get('contacts', []):
                        main_rows.append({
                            'County': '',
                            'Distance': '',
                            'Website': '',
                            'General Emails': f"{contact.get('name', '')} - {contact.get('title', '')}",
                            'Status': 'Contact'
                        })
                else:
                    manual_rows.append({
                        'County': county_name,
                        'Entity Type': dept_name,
                        'Search Suggestion': f'Visit {county_data.get("county_website", "county website")} and look for {dept_name}',
                        'Priority': 'High'
                    })
            
            # Manual research items
            for item in county_data.get('manual_research_needed', []):
                manual_rows.append({
                    'County': county_name,
                    'Entity Type': item['type'],
                    'Search Suggestion': item['suggestion'],
                    'Priority': 'Medium'
                })
        
        # Create Excel with multiple sheets
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Main results sheet
            df_main = pd.DataFrame(main_rows)
            df_main.to_excel(writer, sheet_name='Found Results', index=False)
            
            # Manual research sheet
            df_manual = pd.DataFrame(manual_rows)
            df_manual.to_excel(writer, sheet_name='Manual Research Needed', index=False)
            
            # Format both sheets
            for sheet_name in ['Found Results', 'Manual Research Needed']:
                worksheet = writer.sheets[sheet_name]
                
                # Header formatting
                header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
                header_font = Font(color='FFFFFF', bold=True)
                
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center')
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(cell.value)
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 60)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"✓ Export complete: {filename}")
        return filename
    
    def run(self, radius_miles: int = 200, limit_counties: Optional[int] = None):
        """Run the lead generator"""
        logger.info("="*60)
        logger.info("LEAD GENERATOR V2.0 - PRAGMATIC APPROACH")
        logger.info("="*60)
        logger.info(f"Searching within {radius_miles} miles of Frederick, MD")
        logger.info("Strategy: Direct .gov URLs + intelligent scraping")
        logger.info("="*60)
        
        counties = self.get_counties_near_frederick(radius_miles)
        
        if limit_counties:
            counties = counties[:limit_counties]
            logger.info(f"Limited to first {limit_counties} counties for testing")
        
        logger.info(f"\nProcessing {len(counties)} counties...\n")
        
        all_data = []
        for i, county in enumerate(counties, 1):
            logger.info(f"\nCounty {i}/{len(counties)}")
            
            try:
                county_data = self.process_county(county)
                all_data.append(county_data)
                
                # Save every 5 counties
                if i % 5 == 0:
                    self.export_to_excel(all_data, f'leads_v2_progress_{i}.xlsx')
                    
            except Exception as e:
                logger.error(f"Error processing {county['name']}: {e}")
                continue
        
        # Final export
        output_file = self.export_to_excel(all_data)
        
        # Summary
        found_count = sum(1 for d in all_data if d.get('county_website'))
        dept_count = sum(
            sum(1 for dept in d.get('departments', {}).values() if dept['found'])
            for d in all_data
        )
        
        logger.info("\n" + "="*60)
        logger.info("COMPLETE!")
        logger.info("="*60)
        logger.info(f"Results: {output_file}")
        logger.info(f"Counties processed: {len(all_data)}")
        logger.info(f"County websites found: {found_count}/{len(all_data)}")
        logger.info(f"Departments found: {dept_count}")
        logger.info("="*60)
        logger.info("\nNEXT STEPS:")
        logger.info("1. Review 'Found Results' sheet")
        logger.info("2. Use 'Manual Research Needed' sheet for Google searches")
        logger.info("3. Manually add retirement/hospital/chamber data")
        logger.info("="*60)
        
        return output_file


if __name__ == "__main__":
    generator = PragmaticLeadGenerator()
    
    # Test with 3 counties first
    # Change to limit_counties=None for full run
    generator.run(radius_miles=200, limit_counties=None)
