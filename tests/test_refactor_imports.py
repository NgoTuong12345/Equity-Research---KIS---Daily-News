"""
TDD migration tests — one test per file move.
Each test is written BEFORE the file is moved (RED), then the move makes it GREEN.
Run with: vietnam_news_scraper\\venv\\Scripts\\python.exe tests\\test_refactor_imports.py
"""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Step2PathHelpersTests(unittest.TestCase):
    def test_project_root_importable(self):
        sys.path.insert(0, str(ROOT / 'core_tools' / 'paths'))
        from project_root import PROJECT_ROOT
        self.assertTrue((PROJECT_ROOT / 'reports').is_dir())
        self.assertTrue((PROJECT_ROOT / '.git').is_dir())

    def test_report_paths_importable_from_core_tools(self):
        sys.path.insert(0, str(ROOT / 'core_tools' / 'paths'))
        from report_paths import BASE_DIR, REPORTS_DIR
        self.assertTrue(BASE_DIR.is_dir())


class Step3TemplatesTests(unittest.TestCase):
    def test_templates_exist_in_core_tools(self):
        templates = ROOT / 'core_tools' / 'templates'
        self.assertTrue((templates / 'company-logo.jpg').is_file())
        self.assertTrue((templates / 'image_library').is_dir())

    def test_news_html_template_dir_removed(self):
        self.assertFalse((ROOT / 'news_html_template').is_dir())


class Step4LlmBrainTests(unittest.TestCase):
    def test_summary_rules_importable_from_llm_brain(self):
        sys.path.insert(0, str(ROOT / 'llm_brain' / 'prompts_and_rules'))
        from summary_rules import SECTOR_TITLES, SUBTYPE_TITLES, CATEGORIES
        self.assertIsInstance(SECTOR_TITLES, dict)

    def test_news_title_rules_importable_from_llm_brain(self):
        sys.path.insert(0, str(ROOT / 'llm_brain' / 'prompts_and_rules'))
        from news_title_rules import normalized_item_title
        self.assertTrue(callable(normalized_item_title))

    def test_hsx_agent_extractor_importable_from_llm_brain(self):
        sys.path.insert(0, str(ROOT / 'llm_brain' / 'extractors'))
        import hsx_agent_extractor

    def test_apply_news_title_rules_importable_from_llm_brain(self):
        sys.path.insert(0, str(ROOT / 'llm_brain' / 'extractors'))
        import apply_news_title_rules

    def test_scripts_dir_no_longer_has_rules(self):
        self.assertFalse((ROOT / 'scripts' / 'summary_rules.py').is_file())
        self.assertFalse((ROOT / 'scripts' / 'news_title_rules.py').is_file())


class Step5CoreValidationTests(unittest.TestCase):
    def test_validate_summary_data_in_core_tools(self):
        self.assertTrue((ROOT / 'core_tools' / 'validation' / 'validate_summary_data.py').is_file())

    def test_benchmark_in_core_tools(self):
        self.assertTrue((ROOT / 'core_tools' / 'validation' / 'benchmark_html_against_pdf.py').is_file())

    def test_scripts_dir_no_longer_has_validation(self):
        self.assertFalse((ROOT / 'scripts' / 'validate_summary_data.py').is_file())
        self.assertFalse((ROOT / 'scripts' / 'benchmark_html_against_pdf.py').is_file())
        self.assertFalse((ROOT / 'scripts' / 'report_paths.py').is_file())


class Step6PhasesTests(unittest.TestCase):
    def test_combine_chunks_in_phase_03(self):
        self.assertTrue((ROOT / 'phases' / '03_summarize' / 'combine_chunks.py').is_file())

    def test_deduplicate_in_phase_03(self):
        self.assertTrue((ROOT / 'phases' / '03_summarize' / 'deduplicate_reports.py').is_file())

    def test_fetch_full_articles_in_phase_03(self):
        self.assertTrue((ROOT / 'phases' / '03_summarize' / 'fetch_full_articles.py').is_file())

    def test_generate_html_in_phase_04(self):
        self.assertTrue((ROOT / 'phases' / '04_publish' / 'generate_html_report.py').is_file())

    def test_scripts_dir_removed(self):
        self.assertFalse((ROOT / 'scripts').is_dir())


class Step7ScrapeTests(unittest.TestCase):
    def test_scraper_main_in_phase_01(self):
        self.assertTrue((ROOT / 'phases' / '01_scrape' / 'main.py').is_file())

    def test_hsx_insider_scraper_in_phase_01(self):
        self.assertTrue((ROOT / 'phases' / '01_scrape' / 'hsx_insider_scraper.py').is_file())

    def test_format_hsx_trading_in_phase_01(self):
        self.assertTrue((ROOT / 'phases' / '01_scrape' / 'format_hsx_trading_news.py').is_file())

    def test_venv_in_phase_01(self):
        self.assertTrue((ROOT / 'phases' / '01_scrape' / 'venv').is_dir())

    def test_vietnam_news_scraper_removed(self):
        self.assertFalse((ROOT / 'vietnam_news_scraper').is_dir())


class Step8CurateTests(unittest.TestCase):
    def test_upload_to_sheets_in_phase_02(self):
        self.assertTrue((ROOT / 'phases' / '02_curate' / 'upload-to-sheets.js').is_file())

    def test_package_json_in_phase_02(self):
        self.assertTrue((ROOT / 'phases' / '02_curate' / 'package.json').is_file())

    def test_google_sheets_uploader_removed(self):
        self.assertFalse((ROOT / 'google-sheets-uploader').is_dir())


class Step9OrchestrationTests(unittest.TestCase):
    def test_morning_bat_in_orchestration(self):
        self.assertTrue((ROOT / 'orchestration' / 'run-morning.bat').is_file())

    def test_afternoon_bat_in_orchestration(self):
        self.assertTrue((ROOT / 'orchestration' / 'run-afternoon.bat').is_file())

    def test_old_morning_bat_removed_from_root(self):
        self.assertFalse((ROOT / 'run-morning.bat').is_file())

    def test_old_afternoon_bat_removed_from_root(self):
        self.assertFalse((ROOT / 'run-afternoon.bat').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
