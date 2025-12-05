"""
Configuration file for Lead Generator
Edit these settings to customize the scraping behavior
"""

# GEOGRAPHIC SETTINGS
RADIUS_MILES = 200  # Distance from Frederick County, MD
CENTER_LOCATION = {
    'county': 'Frederick County',
    'state': 'MD',
    'lat': 39.4143,
    'lon': -77.4105
}

# SCRAPING SETTINGS
REQUEST_DELAY = 2  # Seconds between requests (minimum: 2)
PAGE_TIMEOUT = 15  # Seconds to wait for page load
MAX_SEARCH_RESULTS = 5  # Number of search results to check per query
MAX_DEPTH = 3  # How many links deep to follow from main page

# RATE LIMITING
MAX_RETRIES = 3  # Number of retries on failure
RETRY_DELAY = 5  # Seconds to wait before retry
SAVE_INTERVAL = 5  # Save intermediate results every N counties

# OUTPUT SETTINGS
OUTPUT_FILENAME = 'lead_generator_results.xlsx'
LOG_FILENAME = 'lead_generator.log'
SAVE_INTERMEDIATE = True  # Save progress periodically
INTERMEDIATE_PREFIX = 'leads_intermediate'

# DEPARTMENT SEARCH TERMS
# Customize what departments to search for
DEPARTMENTS = [
    'Department of Aging',
    'IT Training',
    'Cybersecurity',
    'Cybersecurity Awareness',
    'Workforce Services',
    'Public Schools Staff Development',
    'Community College Continuing Education',
    'Public Library'
]

# DEPARTMENT SEARCH VARIATIONS
# Add alternative search terms for better results
DEPARTMENT_VARIATIONS = {
    'IT Training': [
        'IT training',
        'information technology training',
        'computer training',
        'technology training'
    ],
    'Cybersecurity': [
        'cybersecurity',
        'cyber security',
        'information security',
        'IT security'
    ],
    'Cybersecurity Awareness': [
        'cybersecurity awareness',
        'security awareness training',
        'cyber awareness'
    ],
    'Department of Aging': [
        'aging services',
        'senior services',
        'office on aging',
        'area agency on aging',
        'department of aging'
    ],
    'Workforce Services': [
        'workforce development',
        'employment services',
        'job services',
        'career services'
    ],
    'Public Schools Staff Development': [
        'professional development',
        'teacher training',
        'staff development',
        'educator training'
    ],
    'Community College Continuing Education': [
        'continuing education',
        'workforce development',
        'adult education',
        'community education'
    ],
    'Public Library': [
        'public library',
        'library system',
        'county library'
    ]
}

# JOB TITLES TO LOOK FOR
TARGET_JOB_TITLES = [
    # General Management
    'director',
    'coordinator',
    'manager',
    'administrator',
    'chief',
    'supervisor',
    'officer',
    'specialist',
    'head',
    'chair',
    
    # Specific Roles
    'activities director',
    'program director',
    'training manager',
    'development director',
    'hr director',
    'compliance officer',
    'education coordinator',
    'adult services manager',
    'adult education coordinator',
    
    # Senior Roles
    'executive director',
    'assistant director',
    'associate director',
    'deputy director',
    'regional director',
    'vice president',
    
    # Healthcare/Retirement
    'community life coordinator',
    'nursing education director',
    'learning and development director',
    
    # IT/Cybersecurity
    'IT training manager',
    'cybersecurity manager',
    'information security officer',
    'IT director'
]

# ENTITY SEARCH LIMITS
MAX_RETIREMENT_COMMUNITIES = 3  # Per county
MAX_HOSPITALS = 3  # Per county
MAX_CHAMBERS = 2  # Per county

# COUNTIES TO PROCESS
# Set to None to process all, or specify a list of county names
SPECIFIC_COUNTIES = None  # Example: ['Frederick County', 'Montgomery County']

# TESTING/DEBUG SETTINGS
TEST_MODE = False  # Set to True for limited testing
TEST_COUNTY_LIMIT = 3  # Number of counties to process in test mode

# EMAIL VALIDATION
# Email domains to exclude (spam/invalid)
EMAIL_BLACKLIST = [
    'example.com',
    'domain.com', 
    'email.com',
    'test.com',
    'yourcompany.com',
    'company.com',
    'yourdomain.com',
    'sample.com',
    'placeholder.com',
    'noreply',
    'no-reply',
    'donotreply',
    'mailer-daemon',
    'postmaster'
]

# EXCEL FORMATTING
EXCEL_HEADER_COLOR = '366092'  # Dark blue
EXCEL_HEADER_TEXT_COLOR = 'FFFFFF'  # White
MAX_COLUMN_WIDTH = 50  # Maximum width for Excel columns

# USER AGENT
# Rotate these if you get blocked
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
]

# LOGGING SETTINGS
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# NOTES FOR CUSTOMIZATION:
# 
# 1. To run faster (less polite):
#    - Decrease REQUEST_DELAY to 1
#    - Increase MAX_SEARCH_RESULTS to 10
#    WARNING: May get blocked more easily
#
# 2. To be more thorough:
#    - Increase MAX_DEPTH to 5
#    - Increase MAX_SEARCH_RESULTS to 10
#    - Add more DEPARTMENT_VARIATIONS
#    WARNING: Will take much longer
#
# 3. For testing:
#    - Set TEST_MODE = True
#    - Set TEST_COUNTY_LIMIT = 1
#
# 4. To process specific counties only:
#    - Set SPECIFIC_COUNTIES = ['Frederick County', 'Montgomery County', ...]
