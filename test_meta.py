import asyncio
from app.api import run_analysis_for_ticker

async def check_meta():
    print("--- Checking Status for Meta (META) ---")
    try:
        # run_analysis_for_ticker handles both fetching and calculating metrics
        result = await run_analysis_for_ticker("META", db=None, save_history=False, skip_external=True)
        
        ticker = result.get("ticker")
        name = result.get("company_name")
        metrics = result.get("metrics", {})
        yearly = metrics.get("yearly", [])
        
        print(f"Ticker: {ticker}")
        print(f"Company Name: {name}")
        print(f"Data Points Found: {len(yearly)} years")
        
        if yearly:
            print("\nRecent Financials (Millions USD):")
            for year_data in yearly[-3:]: # Show last 3 years
                print(f"  {year_data['year']}: Revenue=${year_data['revenue']:.2f}, EBITDA=${year_data['ebitda']:.2f}, Net Income=${year_data['net_income']:.2f}")
            
            print(f"\nKey Indicators:")
            print(f"  Revenue CAGR: {metrics.get('revenue_cagr_pct')}%")
            print(f"  Current Altman Z-Score: {metrics.get('current_z_score')}")
            print(f"  Solvency Signal: {metrics.get('solvency_signal')}")
            print(f"  Color Signal: {result.get('color_signal')}")
        else:
            print("No yearly metrics found.")
            
    except Exception as e:
        print(f"Error checking Meta: {e}")

if __name__ == "__main__":
    asyncio.run(check_meta())
