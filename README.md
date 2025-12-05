# Lead Generator Application

## Overview
Automated lead generation tool that scrapes county government agencies, retirement communities, hospitals, and business associations within a specified radius of Frederick County, MD.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Run (Test with 3 counties)
```bash
python lead_generator.py
```

### Full Run (All counties within 200 miles)
Edit the last line in `lead_generator.py`:
```python
generator.run(radius_miles=200, limit_counties=None)  # Remove limit
```

### Custom Configuration
```python
from lead_generator import LeadGenerator

generator = LeadGenerator()
generator.delay = 3  # Increase delay between requests (default: 2 seconds)
generator.run(radius_miles=150, limit_counties=10)  # Custom radius and limit
```

## Output

The application generates:
- **Excel file**: `lead_generator_results.xlsx` with all findings
- **Log file**: `lead_generator.log` with detailed execution logs
- **Intermediate files**: Saved every 5 counties as backup

### Excel Structure
| County | Distance | Category | Entity Type | Entity Name | Website | Emails | Contacts |
|--------|----------|----------|-------------|-------------|---------|--------|----------|

## Important Limitations

### What This Tool CAN Do:
✅ Find county official websites
✅ Search for specific departments and organizations
✅ Extract visible email addresses from web pages
✅ Extract names that appear near job titles
✅ Organize data into structured Excel format
✅ Handle rate limiting with delays

### What This Tool CANNOT Reliably Do:
❌ **Guarantee email accuracy** - Many sites hide emails or use contact forms
❌ **Find specific personnel** - Job titles may not appear with names/emails
❌ **Access password-protected content** - Staff directories often require login
❌ **Handle all anti-bot measures** - Some sites will block automated access
❌ **Scrape JavaScript-heavy sites** - Would need Selenium (adds complexity)
❌ **Provide 100% coverage** - Some entities won't be found via search

## Expected Results by Category

### Government Departments (50-70% hit rate)
- County websites: HIGH success
- Department pages: MEDIUM success
- Contact emails: LOW-MEDIUM (many use forms)
- Specific personnel: LOW (often requires staff portal access)

### Retirement Communities (60-80% hit rate)
- Facility websites: HIGH success
- General emails: MEDIUM success
- Activities director names: LOW (often not public)

### Hospitals (70-90% hit rate)
- Hospital websites: HIGH success
- Department emails: MEDIUM success
- Specific personnel: LOW (HIPAA/privacy concerns)

### Chambers of Commerce (80-95% hit rate)
- Organization websites: HIGH success
- Contact emails: HIGH success
- Program information: MEDIUM success

## Improving Results

### Manual Enhancement Needed For:
1. **Personnel Names/Emails**: Use LinkedIn Sales Navigator or manual research
2. **Hidden Contact Info**: Call organizations directly
3. **Protected Directories**: Request access to staff portals
4. **Verification**: Always verify before outreach

### Additional Tools to Consider:
- **Hunter.io**: Email finding service
- **Apollo.io**: B2B contact database
- **RocketReach**: Contact information finder
- **Selenium**: For JavaScript-heavy sites (can add if needed)

## Best Practices

1. **Run in batches**: Start with `limit_counties=3` to test
2. **Check intermediate files**: Review quality every 5 counties
3. **Verify critical leads**: Manually confirm high-value contacts
4. **Respect rate limits**: Don't decrease delay below 2 seconds
5. **Monitor logs**: Watch for errors and blocked sites

## Ethical Considerations

- This tool scrapes only PUBLIC information
- Respects robots.txt where possible
- Includes delays to avoid overwhelming servers
- For legitimate business outreach only
- Always comply with CAN-SPAM and GDPR regulations

## Troubleshooting

### "No results found"
- Check internet connection
- Some searches may be blocked - increase `delay`
- Try running at different times of day

### "Connection timeout"
- Increase timeout in `scrape_page()` method
- Check if site requires VPN or specific location

### "Too many requests"
- Increase `self.delay` to 3-5 seconds
- Run in smaller batches

## Customization

### Adding New Search Categories
Edit the `process_county()` method:
```python
# Add after line 280
new_query = f"{county_name} {state} your search term"
new_urls = self.search_google(new_query, num_results=5)
```

### Changing Search Depth
Edit `num_results` parameter in search calls:
```python
urls = self.search_google(query, num_results=10)  # Get more results
```

### Adding Selenium Support
For JavaScript sites, you can add:
```bash
pip install selenium webdriver-manager
```

Then modify scraping methods to use Selenium WebDriver.

## Performance

- **Time per county**: ~3-5 minutes (with delays)
- **Expected runtime**: 
  - 3 counties: ~15 minutes
  - 27 counties: ~2 hours
  - Full 200-mile radius: ~3-4 hours

## Support

Check `lead_generator.log` for detailed execution information and errors.

## Future Enhancements

Potential improvements (require additional work):
- [ ] Selenium integration for JS-heavy sites
- [ ] API integration (Google Places, government data)
- [ ] Natural Language Processing for better name extraction
- [ ] Email validation service integration
- [ ] Automatic retry logic for failed searches
- [ ] Export to CRM-compatible formats
- [ ] Duplicate detection and merging
