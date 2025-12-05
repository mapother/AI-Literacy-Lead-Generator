"""
Lead Generator Application
Scrapes county government and organization data within 200 miles of Frederick, MD
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from typing import List, Dict, Optional
import json
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lead_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LeadGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.results = []
        self.delay = 2  # Polite delay between requests
        
    def get_counties_near_frederick(self, radius_miles: int = 200) -> List[Dict]:
        """
        Get counties within radius of Frederick County, MD
        Using a predefined list for Maryland, Virginia, Pennsylvania, West Virginia, Delaware
        """
        # Frederick, MD coordinates: 39.4143° N, 77.4105° W
        # This is a simplified list - in production, you'd calculate actual distances
        
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
        
        # Filter by radius
        return [c for c in counties if c["distance"] <= radius_miles]
    
    def search_google(self, query: str, num_results: int = 5) -> List[str]:
        """
        Search Google and return URLs (simplified - uses DuckDuckGo HTML)
        Note: Google blocks automated searches. Consider using SerpAPI or similar.
        """
        try:
            # Using DuckDuckGo as it's more scraper-friendly
            search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            urls = []
            for result in soup.find_all('a', {'class': 'result__a'}, limit=num_results):
                url = result.get('href')
                if url and url.startswith('http'):
                    urls.append(url)
            
            time.sleep(self.delay)
            return urls
        except Exception as e:
            logger.error(f"Search error for '{query}': {e}")
            return []
    
    def find_county_website(self, county_name: str, state: str) -> Optional[str]:
        """Find official county website"""
        query = f"{county_name} {state} official government website"
        urls = self.search_google(query, num_results=3)
        
        # Look for official .gov domain
        for url in urls:
            if '.gov' in url and state.lower() in url.lower():
                return url
        
        return urls[0] if urls else None
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        # Filter out common false positives
        emails = [e for e in emails if not any(x in e.lower() for x in ['example.com', 'domain.com', 'email.com'])]
        return list(set(emails))
    
    def extract_names_near_titles(self, text: str, titles: List[str]) -> List[str]:
        """
        Extract names that appear near job titles
        This is a simplified approach - real name extraction is complex
        """
        names = []
        title_pattern = '|'.join([re.escape(t) for t in titles])
        
        # Look for patterns like "Title: Name" or "Name, Title"
        pattern = rf'(?i)(?:{title_pattern})[:\s,]+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        matches = re.findall(pattern, text)
        names.extend(matches)
        
        # Look for "Name, Title" pattern
        pattern = rf'([A-Z][a-z]+\s+[A-Z][a-z]+)[,\s]+(?:{title_pattern})'
        matches = re.findall(pattern, text)
        names.extend(matches)
        
        return list(set(names))
    
    def scrape_page(self, url: str, max_depth: int = 2) -> Dict:
        """
        Scrape a page for emails, names, and relevant links
        """
        result = {
            'url': url,
            'emails': [],
            'names': [],
            'relevant_links': [],
            'text': ''
        }
        
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            result['text'] = text
            
            # Extract emails
            result['emails'] = self.extract_emails(text)
            
            # Extract names near relevant titles
            titles = [
                'Director', 'Coordinator', 'Manager', 'Administrator',
                'Chief', 'Officer', 'Specialist', 'Supervisor'
            ]
            result['names'] = self.extract_names_near_titles(text, titles)
            
            # Find relevant links for deeper scraping
            keywords = ['contact', 'about', 'staff', 'directory', 'team', 'leadership']
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                link_text = link.get_text().lower()
                
                if any(kw in href.lower() or kw in link_text for kw in keywords):
                    full_url = urljoin(url, href)
                    if urlparse(full_url).netloc == urlparse(url).netloc:
                        result['relevant_links'].append(full_url)
            
            time.sleep(self.delay)
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        
        return result
    
    def find_department(self, county_name: str, state: str, dept_name: str) -> Dict:
        """
        Find a specific department for a county
        """
        query = f"{county_name} {state} {dept_name}"
        urls = self.search_google(query, num_results=3)
        
        result = {
            'department': dept_name,
            'found': False,
            'website': None,
            'emails': [],
            'contacts': []
        }
        
        if urls:
            result['website'] = urls[0]
            result['found'] = True
            
            # Scrape the department page
            scraped_data = self.scrape_page(urls[0])
            result['emails'] = scraped_data['emails']
            result['contacts'] = scraped_data['names']
            
            # Try to scrape contact pages
            for link in scraped_data['relevant_links'][:3]:  # Limit depth
                linked_data = self.scrape_page(link)
                result['emails'].extend(linked_data['emails'])
                result['contacts'].extend(linked_data['names'])
        
        # Remove duplicates
        result['emails'] = list(set(result['emails']))
        result['contacts'] = list(set(result['contacts']))
        
        return result
    
    def process_county(self, county: Dict) -> Dict:
        """
        Process a single county and gather all required information
        """
        county_name = county['name']
        state = county['state']
        
        logger.info(f"Processing {county_name}, {state}")
        
        county_data = {
            'county_name': f"{county_name}, {state}",
            'distance': county['distance'],
            'county_website': self.find_county_website(county_name, state),
            'departments': {},
            'retirement_communities': [],
            'hospitals': [],
            'business_associations': []
        }
        
        # Department types to search for
        departments = [
            'Department of Aging',
            'IT Training',
            'Cybersecurity',
            'Cybersecurity Awareness',
            'Workforce Services',
            'Public Schools Staff Development',
            'Community College Continuing Education',
            'Public Library'
        ]
        
        for dept in departments:
            logger.info(f"  Searching for {dept}...")
            dept_data = self.find_department(county_name, state, dept)
            county_data['departments'][dept] = dept_data
            time.sleep(self.delay)  # Be polite
        
        # Find retirement communities
        logger.info(f"  Searching for retirement communities...")
        retirement_query = f"{county_name} {state} retirement community assisted living"
        retirement_urls = self.search_google(retirement_query, num_results=5)
        
        for url in retirement_urls[:3]:  # Limit to top 3
            scraped = self.scrape_page(url)
            community = {
                'name': urlparse(url).netloc.replace('www.', ''),
                'website': url,
                'emails': scraped['emails'],
                'contacts': scraped['names']
            }
            county_data['retirement_communities'].append(community)
            time.sleep(self.delay)
        
        # Find hospitals
        logger.info(f"  Searching for hospitals...")
        hospital_query = f"{county_name} {state} hospital healthcare"
        hospital_urls = self.search_google(hospital_query, num_results=5)
        
        for url in hospital_urls[:3]:  # Limit to top 3
            scraped = self.scrape_page(url)
            hospital = {
                'name': urlparse(url).netloc.replace('www.', ''),
                'website': url,
                'emails': scraped['emails'],
                'contacts': scraped['names']
            }
            county_data['hospitals'].append(hospital)
            time.sleep(self.delay)
        
        # Find chambers of commerce
        logger.info(f"  Searching for chamber of commerce...")
        chamber_query = f"{county_name} {state} chamber of commerce business association"
        chamber_urls = self.search_google(chamber_query, num_results=3)
        
        for url in chamber_urls[:2]:  # Limit to top 2
            scraped = self.scrape_page(url)
            chamber = {
                'name': urlparse(url).netloc.replace('www.', ''),
                'website': url,
                'emails': scraped['emails'],
                'contacts': scraped['names']
            }
            county_data['business_associations'].append(chamber)
            time.sleep(self.delay)
        
        return county_data
    
    def export_to_excel(self, data: List[Dict], filename: str = 'lead_generator_results.xlsx'):
        """
        Export results to a well-formatted Excel file
        """
        logger.info(f"Exporting to {filename}...")
        
        # Flatten data for Excel
        rows = []
        
        for county_data in data:
            county_name = county_data['county_name']
            
            # County info row
            rows.append({
                'County': county_name,
                'Distance (miles)': county_data['distance'],
                'County Website': county_data.get('county_website', ''),
                'Category': 'County Info',
                'Entity Type': '',
                'Entity Name': '',
                'Website': county_data.get('county_website', ''),
                'Emails': '',
                'Contacts': ''
            })
            
            # Department rows
            for dept_name, dept_data in county_data['departments'].items():
                if dept_data['found']:
                    rows.append({
                        'County': county_name,
                        'Distance (miles)': '',
                        'County Website': '',
                        'Category': 'Government Department',
                        'Entity Type': dept_name,
                        'Entity Name': dept_name,
                        'Website': dept_data.get('website', ''),
                        'Emails': '; '.join(dept_data.get('emails', [])),
                        'Contacts': '; '.join(dept_data.get('contacts', []))
                    })
            
            # Retirement communities
            for community in county_data['retirement_communities']:
                rows.append({
                    'County': county_name,
                    'Distance (miles)': '',
                    'County Website': '',
                    'Category': 'Retirement Community',
                    'Entity Type': 'Retirement Community',
                    'Entity Name': community['name'],
                    'Website': community['website'],
                    'Emails': '; '.join(community.get('emails', [])),
                    'Contacts': '; '.join(community.get('contacts', []))
                })
            
            # Hospitals
            for hospital in county_data['hospitals']:
                rows.append({
                    'County': county_name,
                    'Distance (miles)': '',
                    'County Website': '',
                    'Category': 'Hospital/Healthcare',
                    'Entity Type': 'Hospital',
                    'Entity Name': hospital['name'],
                    'Website': hospital['website'],
                    'Emails': '; '.join(hospital.get('emails', [])),
                    'Contacts': '; '.join(hospital.get('contacts', []))
                })
            
            # Business associations
            for chamber in county_data['business_associations']:
                rows.append({
                    'County': county_name,
                    'Distance (miles)': '',
                    'County Website': '',
                    'Category': 'Business Association',
                    'Entity Type': 'Chamber of Commerce',
                    'Entity Name': chamber['name'],
                    'Website': chamber['website'],
                    'Emails': '; '.join(chamber.get('emails', [])),
                    'Contacts': '; '.join(chamber.get('contacts', []))
                })
        
        # Create DataFrame and export
        df = pd.DataFrame(rows)
        
        # Write to Excel with formatting
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Leads', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Leads']
            
            # Format header
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_font = Font(color='FFFFFF', bold=True)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
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
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Export complete: {filename}")
        return filename
    
    def run(self, radius_miles: int = 200, limit_counties: Optional[int] = None):
        """
        Main execution method
        """
        logger.info("Starting Lead Generator...")
        logger.info(f"Searching for counties within {radius_miles} miles of Frederick, MD")
        
        # Get counties
        counties = self.get_counties_near_frederick(radius_miles)
        
        if limit_counties:
            counties = counties[:limit_counties]
            logger.info(f"Limited to first {limit_counties} counties for testing")
        
        logger.info(f"Found {len(counties)} counties to process")
        
        # Process each county
        all_data = []
        for i, county in enumerate(counties, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing county {i}/{len(counties)}")
            logger.info(f"{'='*60}")
            
            try:
                county_data = self.process_county(county)
                all_data.append(county_data)
                
                # Save intermediate results every 5 counties
                if i % 5 == 0:
                    self.export_to_excel(all_data, f'leads_intermediate_{i}.xlsx')
                    
            except Exception as e:
                logger.error(f"Error processing {county['name']}: {e}")
                continue
        
        # Final export
        output_file = self.export_to_excel(all_data)
        
        logger.info("\n" + "="*60)
        logger.info("Lead generation complete!")
        logger.info(f"Results saved to: {output_file}")
        logger.info(f"Processed {len(all_data)} counties")
        logger.info("="*60)
        
        return output_file


if __name__ == "__main__":
    generator = LeadGenerator()
    
    # Start with just 2-3 counties for testing
    # Remove or increase limit_counties for full run
    generator.run(radius_miles=200, limit_counties=3)
