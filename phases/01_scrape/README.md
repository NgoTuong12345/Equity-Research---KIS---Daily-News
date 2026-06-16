# Vietnam Financial News Scraper

This is a self-contained news scraper package. It aggregates recent news articles (looking back 24 hours) from multiple Vietnamese financial news sources, including:
1. **RSS Feeds**: Vietstock, VnEconomy, VietTimes, NhanDan, etc.
2. **TinNhanhChungKhoan**: Multi-category articles (Enterprise, Real Estate, Finance, International, Current Affairs).
3. **BaoDautu**: Multi-category articles (Investment, Banking, Securities, Real Estate, etc.).
4. **FireAnt**: Selenium-based real-time news feed.

Articles are automatically categorized using a robust keyword and URL mapping ruleset.

The output will be saved as a CSV file in the same folder, named like: `vietnam_financial_news_combined_YYYYMMDD_HHMM.csv`.

## Requirements
- Python 3.8 or newer.
- Google Chrome browser installed (required by Selenium for scraping FireAnt).

## How to Run

### Windows
1. Double-click the `run.bat` file.
2. The script will automatically:
   - Verify Python is installed.
   - Create a local virtual environment (`venv`) to prevent library conflicts.
   - Install all required libraries (Pandas, Selenium, BeautifulSoup4, etc.).
   - Execute the scraper.

### macOS / Linux
1. Open a terminal in this directory.
2. Make `run.sh` executable by running:
   ```bash
   chmod +x run.sh
   ```
3. Run the script:
   ```bash
   ./run.sh
   ```
4. The script will automatically create the virtual environment, install requirements, and execute the scraper.

## Package Contents
- `main.py`: The python scraper script.
- `requirements.txt`: The python libraries list.
- `run.bat` / `run.sh`: Setup and run launchers.
- `README.md`: This file.
