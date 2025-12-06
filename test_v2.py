"""
Quick test for Lead Generator V2
Tests with just Frederick County
"""

from lead_generator_v2 import PragmaticLeadGenerator

if __name__ == "__main__":
    print("="*60)
    print("LEAD GENERATOR V2 - SINGLE COUNTY TEST")
    print("="*60)
    print("\nTesting with Frederick County, MD only")
    print("This will take ~2-3 minutes")
    print("="*60)
    
    generator = PragmaticLeadGenerator()
    
    # Just test Frederick County
    test_county = [{"name": "Frederick County", "state": "MD", "distance": 0}]
    
    print("\nStarting test...\n")
    
    try:
        county_data = generator.process_county(test_county[0])
        output_file = generator.export_to_excel([county_data], 'test_frederick_v2.xlsx')
        
        print("\n" + "="*60)
        print("TEST COMPLETE!")
        print("="*60)
        print(f"\nResults: {output_file}")
        
        # Summary
        if county_data.get('county_website'):
            print(f"✓ County website found: {county_data['county_website']}")
            dept_found = sum(1 for d in county_data['departments'].values() if d['found'])
            print(f"✓ Departments found: {dept_found}/{len(county_data['departments'])}")
            total_emails = len(county_data.get('general_emails', []))
            print(f"✓ Emails extracted: {total_emails}")
        else:
            print("✗ County website not found")
        
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("1. Open test_frederick_v2.xlsx")
        print("2. Review the 'Found Results' sheet")
        print("3. If satisfied, run full version:")
        print("   python lead_generator_v2.py")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        print("Check lead_generator_v2.log for details")
