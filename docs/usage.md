# Usage Guide

This guide explains how to use the modules and run projects in Workflow Kaizen.

## General Usage

1. **Activate Virtual Environment**
   ```
   .\venv\Scripts\activate  # or conda activate workflow-kaizen
   ```

2. **Import Modules**
   In your Python script:
   ```python
   from modules.data_scraping.web_scraper import scrape_data
   data = scrape_data('https://example.com')
   ```

3. **Run a Project**
   Navigate to a project folder:
   ```
   cd projects/project-1
   python main.py
   ```

## Module-Specific Usage
- **data-scraping**: See modules/data-scraping/README.md
- **etl-pipeline**: Configure in config.py and run extractor.py

## Best Practices
- Always use relative paths for files.
- Log outputs for debugging.
- Test on target PC (e.g., company computer) before full deployment.
- Update requirements.txt after installing new packages: `pip freeze > requirements.txt`

For detailed examples, check each module's README.

