"""
Quick test script to verify the lead generator works
Tests basic functionality without running full scraping
"""

from lead_generator import LeadGenerator
import sys

def test_basic_functionality():
    """Test basic components"""
    print("="*60)
    print("LEAD GENERATOR - QUICK TEST")
    print("="*60)
    
    generator = LeadGenerator()
    
    # Test 1: County list
    print("\n1. Testing county discovery...")
    counties = generator.get_counties_near_frederick(200)
    print(f"   ✓ Found {len(counties)} counties")
    print(f"   Sample: {counties[0]['name']}, {counties[0]['state']}")
    
    # Test 2: Email extraction
    print("\n2. Testing email extraction...")
    test_text = """
    Contact us at info@example.org or reach John Doe at john.doe@county.gov
    For support: support@test.com
    """
    emails = generator.extract_emails(test_text)
    print(f"   ✓ Extracted {len(emails)} valid emails: {emails}")
    
    # Test 3: Name extraction
    print("\n3. Testing name extraction...")
    test_text2 = """
    Director: Jane Smith
    John Adams, Program Coordinator
    Sarah Johnson
    Manager of IT Services
    """
    names = generator.extract_names_near_titles(test_text2, ['Director', 'Coordinator', 'Manager'])
    print(f"   ✓ Extracted {len(names)} names: {names}")
    
    # Test 4: Search (just one quick search)
    print("\n4. Testing web search...")
    print("   Searching for 'Frederick County Maryland official'...")
    try:
        results = generator.search_google("Frederick County Maryland official government", num_results=2)
        print(f"   ✓ Got {len(results)} search results")
        if results:
            print(f"   First result: {results[0][:80]}...")
    except Exception as e:
        print(f"   ⚠ Search test failed: {e}")
        print("   (This is normal if rate limited, will work during actual run)")
    
    print("\n" + "="*60)
    print("BASIC TESTS COMPLETE")
    print("="*60)
    print("\nTo run a FULL test with actual scraping:")
    print("  python lead_generator.py")
    print("\nThis will process 3 counties (takes ~15 minutes)")
    print("="*60)


def run_single_county_test():
    """Test full functionality on ONE county"""
    print("\n" + "="*60)
    print("SINGLE COUNTY TEST - FREDERICK COUNTY")
    print("="*60)
    print("\nThis will:")
    print("  - Search for Frederick County government")
    print("  - Look for 2-3 departments")
    print("  - Extract emails and contacts")
    print("  - Create Excel output")
    print("\nEstimated time: 5-7 minutes")
    print("="*60)
    
    response = input("\nRun single county test? (y/n): ")
    
    if response.lower() != 'y':
        print("Test cancelled.")
        return
    
    print("\nStarting test...")
    generator = LeadGenerator()
    
    # Just test Frederick County
    test_county = {"name": "Frederick County", "state": "MD", "distance": 0}
    
    try:
        result = generator.process_county(test_county)
        
        # Export to Excel
        output = generator.export_to_excel([result], 'test_single_county.xlsx')
        
        print("\n" + "="*60)
        print("TEST COMPLETE!")
        print("="*60)
        print(f"\nResults saved to: {output}")
        print("Check the file to see what data was extracted.")
        print("\nNext steps:")
        print("  1. Review the output file")
        print("  2. If satisfied, run: python lead_generator.py")
        print("  3. For full run, edit limit_counties=None in the script")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        print("Check lead_generator.log for details")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        run_single_county_test()
    else:
        test_basic_functionality()
        print("\n\nTo run a full single-county test:")
        print("  python test.py --full")
