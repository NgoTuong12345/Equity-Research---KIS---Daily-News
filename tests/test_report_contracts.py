import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "phases" / "04_publish"))
sys.path.insert(0, str(ROOT / "phases" / "01_scrape"))
sys.path.insert(0, str(ROOT / "core_tools" / "paths"))
sys.path.insert(0, str(ROOT / "llm_brain" / "prompts_and_rules"))

import generate_html_report as html_report
import format_hsx_trading_news as trading_news


class ReportContractTests(unittest.TestCase):
    def test_generated_html_uses_paths_relative_to_export_folder(self):
        html = html_report.generate("mor_05_06_2026", "en")

        self.assertIn("../../../../core_tools/templates/image_library/background/mor_intro_background.jpg", html)
        self.assertIn("../../../../core_tools/templates/company-logo.jpg", html)
        self.assertNotIn("url('../core_tools/templates/image_library/background/mor_intro_background.jpg')", html)

    def test_sections_follow_daily_report_order(self):
        sections = html_report.collect_sections("mor_05_06_2026")
        keys = [section["key"] for section in sections]

        self.assertLess(keys.index("macro"), keys.index("trading"))
        self.assertLess(keys.index("trading"), keys.index("commodities"))
        self.assertLess(keys.index("commodities"), keys.index("real_estate"))
        self.assertLess(keys.index("industrials"), keys.index("political"))
        self.assertLess(keys.index("political"), keys.index("policies"))

    def test_corporate_and_trading_headings_use_ticker_company_exchange(self):
        item = {
            "ticker": "VIC",
            "company_en": "Vingroup",
            "exchange": "HSX",
            "title_en": "Long title",
            "summary_en": "Summary",
        }

        corporate = html_report.render_card(item, "en", "Real Estate", category="corporate")
        trading = html_report.render_card(item, "en", "Trading", category="trading")

        self.assertIn("<h3>VIC. (Vingroup. HSX)</h3>", corporate)
        self.assertIn("<h3>VIC. (Vingroup. HSX)</h3>", trading)

    def test_hsx_formatter_deduplicates_repeated_transactions(self):
        record = {
            "ticker": "VIC",
            "source": "HSX",
            "url": "https://example.test/1",
            "date": "2026-06-05",
            "transactions": [
                {
                    "ticker": "VIC",
                    "company_fullname": "Vingroup",
                    "exchange": "HSX",
                    "date_range": "06/09~06/10",
                    "name": "Nguyen Van A",
                    "relationship": "Chu tich HDQT",
                    "action": "buy",
                    "change_volume": "1000",
                    "after_volume": "2000",
                    "after_percentage": "1.0%",
                },
                {
                    "ticker": "VIC",
                    "company_fullname": "Vingroup",
                    "exchange": "HSX",
                    "date_range": "06/09~06/10",
                    "name": "Nguyen Van A",
                    "relationship": "Chu tich HDQT",
                    "action": "buy",
                    "change_volume": "1000",
                    "after_volume": "2000",
                    "after_percentage": "1.0%",
                },
            ],
        }

        items = trading_news.format_records([record])

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["order"], 1)


if __name__ == "__main__":
    unittest.main()
