#!/usr/bin/env python3
"""
Simple test to verify the app components work.
"""

def test_components():
    """Test individual components."""
    try:
        print("🧪 Testing components...")
        
        # Test 1: Import openfootball scraper
        from openfootball_scraper import OpenFootballScraper
        scraper = OpenFootballScraper()
        print("✅ OpenFootball scraper imported")
        
        # Test 2: Import ws_integration
        from ws_integration import get_whoscored_analysis
        print("✅ WS integration imported")
        
        # Test 3: Test analysis generation
        result = get_whoscored_analysis("Manchester City", "Arsenal")
        print(f"✅ Generated {len(result)} opportunities")
        
        # Test 4: Try importing web app (this might fail due to indentation)
        try:
            import web_app
            print("✅ Web app imported successfully")
        except Exception as e:
            print(f"❌ Web app import failed: {e}")
            return False
        
        print("🎉 All components working!")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_components()
    if success:
        print("\n🚀 System is ready for deployment!")
    else:
        print("\n💥 System has issues that need fixing!")
