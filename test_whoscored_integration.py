#!/usr/bin/env python3
"""
Test script for WhoScored integration with existing Bettor system.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_whoscored_import():
    """Test if WhoScored modules can be imported."""
    print("🧪 Testing WhoScored module imports...")
    
    try:
        from ws_pipeline import config, utils, fixtures_scraper, teams_scraper
        from ws_pipeline import transform, features, predict, storage, main
        print("✅ All WhoScored pipeline modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ WhoScored import failed: {e}")
        return False

def test_integration_import():
    """Test if integration module can be imported."""
    print("🧪 Testing integration module import...")
    
    try:
        from ws_integration import WSIntegration, get_whoscored_analysis
        print("✅ WhoScored integration module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Integration import failed: {e}")
        return False

async def test_fixtures_scraping():
    """Test fixtures scraping functionality."""
    print("🧪 Testing fixtures scraping...")
    
    try:
        from ws_pipeline.main import WSPipeline
        
        pipeline = WSPipeline()
        
        # Test cache functionality first
        cache_stats = pipeline.cache.get_cache_stats()
        print(f"   📊 Cache stats: {cache_stats}")
        
        print("   🌐 Attempting to scrape fixtures (this may take 30+ seconds)...")
        print("   ⚠️ Note: This requires internet connection and may be blocked by anti-bot measures")
        
        # Try to scrape fixtures with timeout
        try:
            fixtures_file = await asyncio.wait_for(
                pipeline.run_fixtures_scrape("today"), 
                timeout=60.0
            )
            
            if fixtures_file and Path(fixtures_file).exists():
                print(f"✅ Fixtures scraped successfully: {fixtures_file}")
                
                # Check file content
                import pandas as pd
                df = pd.read_csv(fixtures_file)
                print(f"   📊 Found {len(df)} fixtures")
                
                if len(df) > 0:
                    print(f"   📋 Sample fixture: {df.iloc[0]['home_team_name']} vs {df.iloc[0]['away_team_name']}")
                
                return True
            else:
                print("⚠️ No fixtures file created (may be normal if no matches today)")
                return False
                
        except asyncio.TimeoutError:
            print("⚠️ Fixtures scraping timed out (may be normal due to anti-bot measures)")
            return False
            
    except Exception as e:
        print(f"❌ Fixtures scraping test failed: {e}")
        return False

def test_existing_system_integration():
    """Test integration with existing ESPN system."""
    print("🧪 Testing integration with existing ESPN system...")
    
    try:
        # Test that existing modules still work
        from use_real_espn_rosters import regenerate_with_real_espn_data
        from populate_real_premier_league_matches import main as populate_matches
        
        print("✅ Existing ESPN modules still importable")
        
        # Test enhanced ESPN function
        from use_real_espn_rosters import WHOSCORED_AVAILABLE
        print(f"   🌐 WhoScored integration in ESPN module: {'✅ Available' if WHOSCORED_AVAILABLE else '❌ Not available'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Existing system integration test failed: {e}")
        return False

def test_data_directories():
    """Test that required directories exist."""
    print("🧪 Testing data directories...")
    
    directories = [
        "ws_pipeline/data",
        "ws_pipeline/logs",
        "data"
    ]
    
    all_exist = True
    for directory in directories:
        path = Path(directory)
        if path.exists():
            print(f"✅ {directory} exists")
        else:
            print(f"❌ {directory} missing")
            all_exist = False
    
    return all_exist

async def test_stub_prediction():
    """Test prediction functionality with stub data."""
    print("🧪 Testing prediction functionality...")
    
    try:
        from ws_pipeline import predict, features
        import pandas as pd
        import numpy as np
        
        # Create minimal test data
        players_data = [
            {
                'player_id': 'test_1', 'player_name': 'Test Player 1', 'team_id': 1,
                'goals': 5, 'assists': 3, 'apps_total': 10, 'rating': 7.2,
                'shots_per_game': 2.1, 'pass_success': 0.85
            },
            {
                'player_id': 'test_2', 'player_name': 'Test Player 2', 'team_id': 2,
                'goals': 3, 'assists': 2, 'apps_total': 8, 'rating': 6.8,
                'shots_per_game': 1.8, 'pass_success': 0.82
            }
        ]
        
        team_stats_data = [
            {
                'team_id': 1, 'avg_rating': 7.0, 'total_goals': 25, 'total_assists': 15,
                'avg_shots_per_game': 12.0, 'avg_pass_success': 0.83, 'squad_size': 25
            },
            {
                'team_id': 2, 'avg_rating': 6.8, 'total_goals': 20, 'total_assists': 12,
                'avg_shots_per_game': 10.5, 'avg_pass_success': 0.80, 'squad_size': 23
            }
        ]
        
        players_df = pd.DataFrame(players_data)
        team_stats_df = pd.DataFrame(team_stats_data)
        
        # Test feature creation
        feature_dict = features.create_features_for_fixture(1, 2, players_df, team_stats_df)
        print(f"   📊 Created {len(feature_dict)} features")
        
        # Test prediction
        prediction = predict.predict_fixture(1, 2, players_df, team_stats_df)
        print(f"   🎯 Prediction: Home {prediction['home_win_prob']:.3f}, Draw {prediction['draw_prob']:.3f}, Away {prediction['away_win_prob']:.3f}")
        print(f"   ⚽ Expected scoreline: {prediction['scoreline']}")
        
        # Test player props
        player_props = predict.predict_player_props_for_match(1, 2, players_df, team_stats_df)
        print(f"   👤 Generated {len(player_props)} player prop predictions")
        
        print("✅ Prediction functionality working")
        return True
        
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")
        return False

def test_cli_interface():
    """Test CLI interface."""
    print("🧪 Testing CLI interface...")
    
    try:
        import subprocess
        
        # Test help command
        result = subprocess.run([
            sys.executable, "-m", "ws_pipeline", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "WhoScored scraper pipeline" in result.stdout:
            print("✅ CLI interface working")
            return True
        else:
            print(f"❌ CLI test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting WhoScored Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_whoscored_import),
        ("Integration Import", test_integration_import),
        ("Data Directories", test_data_directories),
        ("Existing System Integration", test_existing_system_integration),
        ("CLI Interface", test_cli_interface),
        ("Stub Prediction", test_stub_prediction),
        ("Fixtures Scraping", test_fixtures_scraping),  # This one may fail due to anti-bot
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! WhoScored integration is ready.")
    elif passed >= total * 0.7:
        print("⚠️ Most tests passed. Integration is mostly working.")
        print("   Note: Fixtures scraping may fail due to anti-bot measures - this is normal.")
    else:
        print("❌ Multiple test failures. Check the setup and dependencies.")
    
    return passed >= total * 0.7

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
