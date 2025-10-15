import requests
import pandas as pd
import json
import os
import time  # For delay to avoid rate limiting
import argparse
import platform
from pathlib import Path

import xml.etree.ElementTree as ET
# Selenium for robust CSV export via button click - cross-platform support
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Cross-platform WebDriver imports
if platform.system() == "Windows":
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService
else:
    # For Mac/Linux development, use Chrome as fallback
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService

# WebDriver manager for automatic driver installation
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# ECHA Annex base URLs and POST parameters
ANNEX_CONFIG = {
    'svhc': {
        'base_url': 'https://echa.europa.eu/candidate-list-table',
        'post_url': 'https://echa.europa.eu/candidate-list-table',
        'params': {
            'p_p_id': 'disslists_WAR_disslistsportlet',
            'p_p_lifecycle': '2',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_resource_id': 'exportResults',
            'p_p_cacheability': 'cacheLevelPage'
        },
        'export_button_id': '#_disslists_WAR_disslistsportlet_exportButtonCSV',
        'export_selector': '#_disslists_WAR_disslistsportlet_exportButtonCSV',
        'csv_filename': 'candidate-list-of-svhc-for-authorisation-export.csv',
        'xml_selector': '#_disslists_WAR_disslistsportlet_exportButtonXML',
        'xml_filename': 'candidate-list-of-svhc-for-authorisation-export.xml'
    },
    'annex_xiv': {
        'base_url': 'https://echa.europa.eu/authorisation-list',
        'post_url': 'https://echa.europa.eu/authorisation-list',  # Adjust based on Network tab
        'params': {  # Similar params, customize if different
            'p_p_id': 'disslists_WAR_disslistsportlet',
            'p_p_lifecycle': '2',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_resource_id': 'exportResults',
            'p_p_cacheability': 'cacheLevelPage'
        },
        'export_selector': '#_disslists_WAR_disslistsportlet_exportButtonCSV',
        'csv_filename': 'authorisation-list-export.csv',
        'xml_selector': '#_disslists_WAR_disslistsportlet_exportButtonXML',
        'xml_filename': 'authorisation-list-export.xml'
    },
    'annex_xvii': {
        'base_url': 'https://echa.europa.eu/substances-restricted-under-reach',
        'post_url': 'https://echa.europa.eu/substances-restricted-under-reach',  # Adjust
        'params': {  # Customize based on site
            'p_p_id': 'disslists_WAR_disslistsportlet',
            'p_p_lifecycle': '2',
            'p_p_state': 'normal',
            'p_p_mode': 'view',
            'p_p_resource_id': 'exportResults',
            'p_p_cacheability': 'cacheLevelPage'
        },
        'export_selector': '#_disslists_WAR_disslistsportlet_exportButtonCSV',
        'csv_filename': 'restriction-list-export.csv',
        'xml_selector': '#_disslists_WAR_disslistsportlet_exportButtonXML',
        'xml_filename': 'restriction-list-export.xml'
    }
}

def _default_headers(base_url: str) -> dict:
    """Return browser-like headers for ECHA requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': base_url,
        'Connection': 'keep-alive',
    }


def _post_headers(base_url: str) -> dict:
    """Headers for CSV export POST call."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36',
        'Accept': 'text/csv,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://echa.europa.eu',
        'Referer': base_url,
    }


def download_csv(annex_type):
    """Download CSV using POST request to simulate export button, with retries and browser-like headers."""
    config = ANNEX_CONFIG.get(annex_type)
    if not config:
        raise ValueError(f"Unknown annex type: {annex_type}")
    
    session = requests.Session()
    base_headers = _default_headers(config['base_url'])

    # First GET the page to get cookies/session (with retries)
    last_exc = None
    for attempt in range(3):
        try:
            response = session.get(config['base_url'], headers=base_headers, timeout=30, allow_redirects=True)
            if response.status_code == 200:
                break
            last_exc = Exception(f"GET {config['base_url']} -> {response.status_code}")
        except Exception as e:
            last_exc = e
        time.sleep(1.5 * (attempt + 1))
    else:
        raise Exception(f"Failed to access base URL: {config['base_url']} ({last_exc})")

    time.sleep(1)  # Delay to mimic user behavior

    # POST to export (with retries)
    post_headers = _post_headers(config['base_url'])
    response = None
    for attempt in range(3):
        try:
            response = session.post(
                config['post_url'],
                params=config['params'],
                headers=post_headers,
                timeout=60,
                allow_redirects=True,
            )
            # Some servers may not set content-type correctly; try to accept on success + non-empty body
            content_type = (response.headers.get('Content-Type') or '').lower()
            if response.status_code == 200 and (('text/csv' in content_type) or (response.content and len(response.content) > 100)):
                break
        except Exception as e:
            last_exc = e
        time.sleep(2.0 * (attempt + 1))
    else:
        raise Exception(f"Failed to download CSV for {annex_type} (last error: {last_exc})")

    # Use pathlib for cross-platform path handling
    data_dir = Path('data')
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_file = data_dir / config['csv_filename']
    
    with open(csv_file, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded: {csv_file}")
    return str(csv_file)


def _build_webdriver(download_dir: Path):
    """Create cross-platform WebDriver in headless mode with download directory configured."""
    system = platform.system()

    # Browser priority: Chrome first (cross-platform), then Edge on Windows
    browser_configs = []

    if system == "Windows":
        browser_configs = [
            (ChromeOptions, webdriver.Chrome, "Chrome"),
            (EdgeOptions, webdriver.Edge, "Edge")
        ]
    else:
        # Mac/Linux: Chrome primarily
        browser_configs = [
            (ChromeOptions, webdriver.Chrome, "Chrome")
        ]

    # Common options for all browsers
    def setup_options(opts):
        opts.add_argument('--headless=new')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-web-security')
        opts.add_argument('--allow-running-insecure-content')

        # Ensure downloads go to the specified folder without prompts
        download_path = str(download_dir.resolve())
        prefs = {
            'download.default_directory': download_path,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
        }
        opts.add_experimental_option('prefs', prefs)
        return opts, download_path

    # Try each browser configuration
    last_error = None
    for opts_class, driver_class, browser_name in browser_configs:
        try:
            opts, download_path = setup_options(opts_class())

            # Set up service with webdriver-manager
            if browser_name == "Chrome":
                service = ChromeService(ChromeDriverManager().install())
            elif browser_name == "Edge":
                service = EdgeService(EdgeChromiumDriverManager().install())
            else:
                service = None

            # Initialize driver with service if available
            if service:
                driver = driver_class(service=service, options=opts)
            else:
                driver = driver_class(options=opts)

            # Force download behavior via CDP (Chromium-based browsers)
            driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                'behavior': 'allow',
                'downloadPath': download_path
            })
            print(f"Successfully initialized {browser_name} WebDriver")
            return driver
        except Exception as e:
            last_error = e
            print(f"{browser_name} WebDriver initialization failed: {e}")
            continue

    # All browsers failed
    error_msg = f"All WebDriver initializations failed. Last error: {last_error}"
    if system == "Windows":
        error_msg += "\nMake sure Chrome or Edge WebDriver is installed. Try: pip install webdriver-manager"
    else:
        error_msg += "\nMake sure Chrome WebDriver is installed. Try: pip install webdriver-manager"
    raise Exception(error_msg)


def _wait_for_new_csv(download_dir: Path, before_files: set[str], timeout: int = 120) -> Path:
    """Wait for a new CSV file to appear and finish downloading in download_dir."""
    end_time = time.time() + timeout
    crdownload_suffix = '.crdownload'
    while time.time() < end_time:
        current_files = {p.name for p in download_dir.glob('*.csv')}
        new_csvs = current_files - before_files
        # If csv visible and no .crdownload present, return the newest
        if new_csvs and not any(download_dir.glob(f'*{crdownload_suffix}')):
            # Choose the most recently modified new CSV
            candidates = sorted(
                [download_dir / name for name in new_csvs],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            return candidates[0]
        time.sleep(0.5)
    raise TimeoutError('CSV download did not complete within timeout')


def download_csv_selenium(annex_type: str) -> str:
    """Use Selenium (Edge headless) to click Export CSV button and wait for file to download."""
    config = ANNEX_CONFIG.get(annex_type)
    if not config:
        raise ValueError(f"Unknown annex type: {annex_type}")

    download_dir = Path('data')
    download_dir.mkdir(parents=True, exist_ok=True)

    driver = _build_webdriver(download_dir)
    try:
        driver.get(config['base_url'])
        wait = WebDriverWait(driver, 30)
        export_selector = config.get('export_selector')
        if not export_selector:
            raise ValueError('export_selector not configured')

        before_files = {p.name for p in download_dir.glob('*.csv')}

        # Try multiple selectors for robustness
        selectors = [
            export_selector,
            '#_disslists_WAR_disslistsportlet_exportButtonCSV',
            'button[id$="exportButtonCSV"]',
            'a[id$="exportButtonCSV"]',
            'button[title*="CSV"]',
        ]

        # Handle disclaimer/terms acceptance first (required for ECHA)
        try:
            disclaimer_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, '_viewsubstances_WAR_echarevsubstanceportlet_acceptDisclaimerButton'))
            )
            disclaimer_button.click()
            print("Accepted disclaimer terms")
            time.sleep(2)  # Wait for page to update after accepting terms
        except TimeoutException:
            print("No disclaimer button found or already accepted")
        except Exception as e:
            print(f"Error accepting disclaimer: {e}")

        # Handle potential cookie banner (best-effort)
        try:
            cookie_buttons = [
                (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler'),
                (By.CSS_SELECTOR, 'button[aria-label*="Accept"]'),
                (By.XPATH, "//button[contains(translate(., 'ACEPT', 'acept'), 'accept') or contains(., 'Accept all')]")
            ]
            for by, sel in cookie_buttons:
                try:
                    el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, sel)))
                    el.click()
                    break
                except TimeoutException:
                    continue
                except Exception:
                    pass
        except Exception:
            pass

        clicked = False
        last_err = None
        for sel in selectors:
            try:
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                driver.execute_script('arguments[0].scrollIntoView({block:"center"});', button)
                button.click()
                clicked = True
                break
            except Exception as e:
                last_err = e
                continue
        if not clicked:
            raise last_err or RuntimeError('Export button not found')

        downloaded_path = _wait_for_new_csv(download_dir, before_files, timeout=180)
        print(f"Downloaded via Selenium: {downloaded_path}")
        return str(downloaded_path)
    finally:
        driver.quit()


def download_xml_selenium(annex_type: str) -> str:
    """Use Selenium to click Export XML button and wait for file to download."""
    config = ANNEX_CONFIG.get(annex_type)
    if not config:
        raise ValueError(f"Unknown annex type: {annex_type}")

    download_dir = Path('data')
    download_dir.mkdir(parents=True, exist_ok=True)

    driver = _build_webdriver(download_dir)
    try:
        driver.get(config['base_url'])
        wait = WebDriverWait(driver, 30)
        export_selector = config.get('xml_selector')
        if not export_selector:
            raise ValueError('xml_selector not configured')

        before_files = {p.name for p in download_dir.glob('*.xml')}

        # Handle disclaimer/terms acceptance first (required for ECHA)
        try:
            disclaimer_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, '_viewsubstances_WAR_echarevsubstanceportlet_acceptDisclaimerButton'))
            )
            disclaimer_button.click()
            print("Accepted disclaimer terms")
            time.sleep(2)  # Wait for page to update after accepting terms
        except TimeoutException:
            print("No disclaimer button found or already accepted")
        except Exception as e:
            print(f"Error accepting disclaimer: {e}")

        # Handle potential cookie banner (best-effort)
        try:
            cookie_buttons = [
                (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler'),
                (By.CSS_SELECTOR, 'button[aria-label*="Accept"]'),
                (By.XPATH, "//button[contains(translate(., 'ACEPT', 'acept'), 'accept') or contains(., 'Accept all')]")
            ]
            for by, sel in cookie_buttons:
                try:
                    el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, sel)))
                    el.click()
                    break
                except TimeoutException:
                    continue
                except Exception:
                    pass
        except Exception:
            pass

        # Try to click XML export button
        clicked = False
        last_err = None
        selectors = [export_selector, 'button[id$="exportButtonXML"]', 'a[id$="exportButtonXML"]', 'button[title*="XML"]']
        for sel in selectors:
            try:
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                driver.execute_script('arguments[0].scrollIntoView({block:"center"});', button)

                # If button is not visible, try JavaScript click
                if not button.is_displayed():
                    print(f"Button not visible, trying JavaScript click for selector: {sel}")
                    driver.execute_script('arguments[0].click();', button)
                else:
                    button.click()

                clicked = True
                print(f"Successfully clicked XML export button with selector: {sel}")
                break
            except Exception as e:
                last_err = e
                print(f"Failed to click with selector {sel}: {e}")
                continue
        if not clicked:
            raise last_err or RuntimeError('XML Export button not found')

        # Wait for XML (modify _wait_for_new_csv to _wait_for_new_file with *.xml)
        def _wait_for_new_xml(download_dir: Path, before_files: set[str], timeout: int = 180) -> Path:
            end_time = time.time() + timeout
            while time.time() < end_time:
                current_files = {p.name for p in download_dir.glob('*.xml')}
                new_xmls = current_files - before_files
                if new_xmls and not any(download_dir.glob('*.crdownload')):
                    candidates = sorted([download_dir / name for name in new_xmls], key=lambda p: p.stat().st_mtime, reverse=True)
                    return candidates[0]
                time.sleep(0.5)
            raise TimeoutError('XML download did not complete within timeout')

        downloaded_path = _wait_for_new_xml(download_dir, before_files)
        print(f"Downloaded XML via Selenium: {downloaded_path}")
        return str(downloaded_path)
    finally:
        driver.quit()


def _read_csv_robust(path: str):
    """Try multiple encodings and delimiter detection before giving up - Windows compatible."""
    # Windows-friendly encoding candidates
    candidates = [
        ('utf-8', None),
        ('utf-8-sig', None),
        ('cp1252', None),  # Windows default encoding
        ('latin-1', None),
        ('utf-8', ','),
        ('utf-8', ';'),
        ('utf-8', '\t'),
        ('cp1252', ','),   # Windows with comma delimiter
        ('cp1252', ';'),   # Windows with semicolon delimiter
    ]
    last_err = None
    for enc, delim in candidates:
        try:
            if delim:
                df = pd.read_csv(path, encoding=enc, sep=delim, engine='python')
            else:
                # Let pandas sniff delimiter
                df = pd.read_csv(path, encoding=enc)
            if not df.empty:
                print(f"Successfully read CSV with encoding: {enc}, delimiter: {delim or 'auto'}")
                return df
        except Exception as e:
            last_err = e
            continue
    print(f"CSV read failed with last error: {last_err}")
    return None

def etl_process(annex_type, skip_download=False):
    """ETL for a specific annex using XML only: Download via Selenium, parse XML, return as dict."""
    config = ANNEX_CONFIG.get(annex_type)
    xml_file = f"data/{config['xml_filename']}"

    # Extract: XML only
    if skip_download:
        if not os.path.exists(xml_file):
            raise FileNotFoundError(f"Existing XML not found for {annex_type}: {xml_file}")
    else:
        xml_file = download_xml_selenium(annex_type)

    # Transform: Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data = []
    for row in root.findall('.//result'):
        row_dict = {}
        for col in row:
            key = col.tag.lower().replace(' ', '_').replace('.', '_')
            row_dict[key] = col.text.strip() if col.text else None
        data.append(row_dict)

    if not data:
        raise ValueError(f"Empty XML for {annex_type}: {xml_file}")

    metadata = {
        'annex_type': annex_type,
        'item_count': len(data),
        'source': config['base_url']
    }
    return {'metadata': metadata, 'data': data}

def main():
    parser = argparse.ArgumentParser(description='REACH ETL Pipeline')
    parser.add_argument('--skip-download', action='store_true', help='Skip downloading CSVs and use existing files')
    args = parser.parse_args()

    os.makedirs('data', exist_ok=True)
    
    all_data = {}
    for annex in ['svhc', 'annex_xiv', 'annex_xvii']:
        try:
            all_data[annex] = etl_process(annex, skip_download=args.skip_download)
            print(f"Processed {annex}")
        except Exception as e:
            print(f"Error processing {annex}: {e}")
    
    json_file = 'data/reach_data.json'
    with open(json_file, 'w') as f:
        json.dump(all_data, f, indent=4)
    print(f"Saved to {json_file}")

if __name__ == "__main__":
    main()
