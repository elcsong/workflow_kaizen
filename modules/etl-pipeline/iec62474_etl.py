#!/usr/bin/env python3
"""
IEC62474 Declarable Substances ETL Script

This script extracts, transforms, and loads IEC62474 Declarable Substances data.
It downloads XML data from the IEC62474 database and converts it to structured JSON format.

IEC62474 integrates multiple regulations including:
- RoHS (Restriction of Hazardous Substances)
- REACH (SVHC, Annex XIV, Annex XVII)
- GADSL (Global Automotive Declarable Substance List)
- Conflict Minerals (3TG)
- EU POPs (Persistent Organic Pollutants)
- SCIP Database

Author: AI Assistant
Date: 2025-10-27
Version: 2.0
"""

import json
import os
import time
import argparse
import platform
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Cross-platform WebDriver imports
if platform.system() == "Windows":
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService
else:
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService

# WebDriver manager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# IEC62474 Configuration
IEC62474_CONFIG = {
    'base_url': 'https://std.iec.ch/iec62474/iec62474.nsf/$DeclarableSubstances?OpenForm',
    'xml_button_id': 'btnExportExcel_1',  # "Export all in XML" button
    'excel_button_id': 'btnExportExcel',  # "Export all" (Excel) button
    'xml_filename': 'IEC62474_DeclarableSubstances.xml',
    'json_filename': 'iec62474_substances.json',  # Fixed filename, always latest
}


class IEC62474EtlProcessor:
    """ETL processor for IEC62474 Declarable Substances data."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the ETL processor.

        Args:
            data_dir: Directory to store downloaded and output files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # JSON files are saved directly in data_dir (like reach_data.json)
        self.json_dir = self.data_dir
        
        self.download_dir = self.data_dir / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _build_webdriver(self, download_dir: Path):
        """Create cross-platform WebDriver in headless mode with download directory configured."""
        system = platform.system()

        # Browser priority: Chrome first (cross-platform), then Edge on Windows
        browser_configs = []

        if system == "Windows":
            browser_configs = [
                (ChromeOptions, webdriver.Chrome, ChromeDriverManager, "Chrome"),
                (EdgeOptions, webdriver.Edge, EdgeChromiumDriverManager, "Edge")
            ]
        else:
            # Mac/Linux: Chrome primarily
            browser_configs = [
                (ChromeOptions, webdriver.Chrome, ChromeDriverManager, "Chrome")
            ]

        # Common options for all browsers
        def setup_options(opts):
            opts.add_argument('--headless=new')
            opts.add_argument('--disable-gpu')
            opts.add_argument('--no-sandbox')
            opts.add_argument('--disable-dev-shm-usage')
            opts.add_argument('--disable-web-security')
            opts.add_argument('--allow-running-insecure-content')
            opts.add_argument('--window-size=1920,1080')

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
        for opts_class, driver_class, manager_class, browser_name in browser_configs:
            try:
                opts, download_path = setup_options(opts_class())

                # Set up service with webdriver-manager
                service = None
                if manager_class == ChromeDriverManager:
                    service = ChromeService(manager_class().install())
                elif manager_class == EdgeChromiumDriverManager:
                    service = EdgeService(manager_class().install())

                # Initialize driver
                if service:
                    driver = driver_class(service=service, options=opts)
                else:
                    driver = driver_class(options=opts)

                # Force download behavior via CDP (Chromium-based browsers)
                driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                    'behavior': 'allow',
                    'downloadPath': download_path
                })
                logger.info(f"Successfully initialized {browser_name} WebDriver")
                return driver
            except Exception as e:
                last_error = e
                logger.warning(f"{browser_name} WebDriver initialization failed: {e}")
                continue

        # All browsers failed
        error_msg = f"All WebDriver initializations failed. Last error: {last_error}"
        if system == "Windows":
            error_msg += "\nMake sure Chrome or Edge WebDriver is installed."
        else:
            error_msg += "\nMake sure Chrome WebDriver is installed."
        raise Exception(error_msg)

    def _wait_for_new_xml(self, download_dir: Path, before_files: set[str], timeout: int = 120) -> Path:
        """Wait for a new XML file to appear and finish downloading in download_dir."""
        end_time = time.time() + timeout
        crdownload_suffix = '.crdownload'
        
        while time.time() < end_time:
            current_files = {p.name for p in download_dir.glob('*.xml')}
            new_xmls = current_files - before_files
            
            # If XML visible and no .crdownload present, return the newest
            if new_xmls and not any(download_dir.glob(f'*{crdownload_suffix}')):
                # Choose the most recently modified new XML
                candidates = sorted(
                    [download_dir / name for name in new_xmls],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                return candidates[0]
            time.sleep(0.5)
        
        raise TimeoutError('XML download did not complete within timeout')

    def download_xml(self) -> str:
        """
        Download IEC62474 XML data using Selenium.
        
        Returns:
            Path to the downloaded XML file
        """
        logger.info("Starting XML download from IEC62474...")
        
        driver = self._build_webdriver(self.download_dir)
        
        try:
            # Navigate to IEC62474 page
            logger.info(f"Navigating to {IEC62474_CONFIG['base_url']}")
            driver.get(IEC62474_CONFIG['base_url'])
            
            # Wait for page to load
            wait = WebDriverWait(driver, 30)
            
            # Handle potential cookie banner
            try:
                cookie_buttons = [
                    (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler'),
                    (By.CSS_SELECTOR, 'button[aria-label*="Accept"]'),
                    (By.XPATH, "//button[contains(translate(., 'ACEPT', 'acept'), 'accept')]")
                ]
                for by, sel in cookie_buttons:
                    try:
                        el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((by, sel)))
                        el.click()
                        logger.info("Accepted cookie banner")
                        break
                    except TimeoutException:
                        continue
            except Exception:
                pass

            # Get list of files before clicking download
            before_files = {p.name for p in self.download_dir.glob('*.xml')}

            # Find and click the "Export all in XML" button
            logger.info("Looking for XML export button...")
            
            # Try multiple selectors for the XML export button
            xml_button_selectors = [
                (By.ID, IEC62474_CONFIG['xml_button_id']),
                (By.CSS_SELECTOR, f"#{IEC62474_CONFIG['xml_button_id']}"),
                (By.XPATH, f"//input[@id='{IEC62474_CONFIG['xml_button_id']}']"),
                (By.XPATH, "//input[@value='Export all in XML']"),
                (By.XPATH, "//button[contains(text(), 'Export all in XML')]"),
            ]

            clicked = False
            for by, selector in xml_button_selectors:
                try:
                    logger.info(f"Trying selector: {by} = {selector}")
                    button = wait.until(EC.element_to_be_clickable((by, selector)))
                    driver.execute_script('arguments[0].scrollIntoView({block:"center"});', button)
                    time.sleep(1)
                    
                    # Try clicking with JavaScript if regular click fails
                    try:
                        button.click()
                    except Exception:
                        driver.execute_script('arguments[0].click();', button)
                    
                    clicked = True
                    logger.info("Successfully clicked XML export button")
                    break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            if not clicked:
                raise RuntimeError('XML Export button not found with any selector')

            # Wait for download link to appear and click it
            logger.info("Waiting for download link to appear...")
            time.sleep(2)  # Give time for the download link to appear
            
            download_link_selectors = [
                (By.XPATH, "//a[contains(@href, 'A_Export_DeclarableSubstances_XML')]"),
                (By.XPATH, "//a[contains(text(), 'Download')]"),
                (By.CSS_SELECTOR, "a[href*='A_Export_DeclarableSubstances_XML']"),
            ]
            
            download_link_clicked = False
            for by, selector in download_link_selectors:
                try:
                    logger.info(f"Trying download link selector: {by} = {selector}")
                    download_link = wait.until(EC.element_to_be_clickable((by, selector)))
                    driver.execute_script('arguments[0].scrollIntoView({block:"center"});', download_link)
                    time.sleep(1)
                    
                    # Click the download link
                    try:
                        download_link.click()
                    except Exception:
                        driver.execute_script('arguments[0].click();', download_link)
                    
                    download_link_clicked = True
                    logger.info("Successfully clicked download link")
                    break
                except Exception as e:
                    logger.debug(f"Download link selector {selector} failed: {e}")
                    continue
            
            if not download_link_clicked:
                raise RuntimeError('Download link not found after clicking XML export button')

            # Wait for download to complete
            logger.info("Waiting for XML download to complete...")
            downloaded_path = self._wait_for_new_xml(self.download_dir, before_files, timeout=180)
            
            logger.info(f"Successfully downloaded XML to: {downloaded_path}")
            return str(downloaded_path)
            
        finally:
            driver.quit()

    def parse_xml(self, xml_file: str) -> Dict[str, Any]:
        """
        Parse IEC62474 XML file and extract substance data.
        
        Args:
            xml_file: Path to the XML file
            
        Returns:
            Dictionary containing parsed substance data
        """
        logger.info(f"Parsing XML file: {xml_file}")
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            substances = []
            substance_groups = {}
            regulations_set = set()
            
            # Parse XML structure - IEC62474 uses <el> tags for each substance
            substance_elements = root.findall('.//el')
            
            logger.info(f"Found {len(substance_elements)} substance elements in XML")
            
            for substance_elem in substance_elements:
                substance_data = self._parse_substance_element(substance_elem)
                if substance_data:
                    substances.append(substance_data)
                    
                    # Track regulations
                    if 'regulations' in substance_data:
                        regulations_set.update(substance_data['regulations'].keys())
                    
                    # Track substance groups
                    group = substance_data.get('substance_group', 'Other')
                    if group not in substance_groups:
                        substance_groups[group] = []
                    substance_groups[group].append(substance_data['name'])
            
            # Build result
            result = {
                'substances': substances,
                'substance_groups': substance_groups,
                'regulations': sorted(list(regulations_set)),
                'total_substances': len(substances)
            }
            
            logger.info(f"Parsed {len(substances)} substances from XML")
            return result
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            raise

    def _parse_substance_element(self, elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parse a single substance XML element from IEC62474 format.
        
        Args:
            elem: XML element representing a substance (<el> tag)
            
        Returns:
            Dictionary containing substance data
        """
        try:
            substance = {}
            
            # Extract basic information from IEC62474 XML structure
            substance['id'] = elem.findtext('ID', '').strip()
            substance['name'] = elem.findtext('SpecificSubstance', '').strip()
            substance['cas_number'] = elem.findtext('CASnumber', '').strip()
            substance['substance_group'] = elem.findtext('SubstanceGroup', '').strip() or 'Other'
            
            # Extract clarification and synonyms
            substance['clarification'] = elem.findtext('SubstanceClarification', '').strip()
            substance['common_synonyms'] = elem.findtext('CommonSynonyms', '').strip()
            
            # Parse alternative names from synonyms
            synonyms_text = substance['common_synonyms']
            if synonyms_text:
                # Split by semicolon and clean up
                alt_names = [name.strip() for name in synonyms_text.split(';') if name.strip()]
                substance['alternative_names'] = alt_names
            else:
                substance['alternative_names'] = []
            
            # Extract application and reporting information
            substance['typical_applications'] = elem.findtext('TypicalApplications', '').strip()
            substance['reportable_applications'] = elem.findtext('ReportableApplications', '').strip()
            substance['reporting_threshold'] = elem.findtext('ReportingThreshold', '').strip()
            substance['reporting_level'] = elem.findtext('ReportingLevel', '').strip()
            substance['reporting_requirement'] = elem.findtext('ReportingRequirement', '').strip()
            
            # Extract basis (regulation source)
            substance['basis'] = elem.findtext('Basis', '').strip()
            substance['basis_description'] = elem.findtext('BasisDescription', '').strip()
            
            # Extract dates
            substance['first_added'] = elem.findtext('FirstAdded', '').strip()
            substance['last_revised'] = elem.findtext('LastRevised', '').strip()
            
            # Extract comments
            substance['comments'] = elem.findtext('Comments', '').strip()
            
            # Parse regulations from basis_description
            regulations = self._parse_regulations_from_basis(substance['basis_description'])
            substance['regulations'] = regulations
            
            # Only return if we have at least a name
            if substance.get('name') and substance['name'] not in ['See Reference Substance worksheet for more details', '']:
                return substance
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing substance element: {e}")
            return None
    
    def _parse_regulations_from_basis(self, basis_description: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract regulation information from basis description.
        
        Args:
            basis_description: Text describing the regulatory basis
            
        Returns:
            Dictionary of regulations
        """
        regulations = {}
        
        if not basis_description:
            return regulations
        
        # Check for RoHS
        if 'RoHS' in basis_description or 'Directive 2011/65/EU' in basis_description:
            regulations['RoHS'] = {'source': 'EU Directive 2011/65/EU'}
        
        # Check for REACH
        if 'REACH' in basis_description:
            reach_info = {'source': 'EU Regulation (EC) No.1907/2006'}
            
            if 'Candidate List' in basis_description or 'SVHC' in basis_description:
                reach_info['svhc'] = True
            
            if 'ANNEX XVII' in basis_description:
                reach_info['annex_xvii'] = True
            
            if 'ANNEX XIV' in basis_description or 'Authorisation' in basis_description:
                reach_info['annex_xiv'] = True
            
            regulations['REACH'] = reach_info
        
        # Check for GADSL
        if 'GADSL' in basis_description or 'Global Automotive' in basis_description:
            regulations['GADSL'] = {'source': 'Global Automotive Declarable Substance List'}
        
        # Check for Conflict Minerals
        if 'Conflict Mineral' in basis_description or 'Dodd-Frank' in basis_description:
            regulations['ConflictMinerals'] = {'source': 'US Dodd-Frank Act'}
        
        # Check for POPs
        if 'POPs' in basis_description or 'Persistent Organic Pollutants' in basis_description:
            regulations['POPs'] = {'source': 'EU Regulation (EC) No.850/2004'}
        
        # Check for other regulations
        if 'TSCA' in basis_description:
            regulations['TSCA'] = {'source': 'US Toxic Substances Control Act'}
        
        if 'California Proposition 65' in basis_description or 'Prop 65' in basis_description:
            regulations['Prop65'] = {'source': 'California Proposition 65'}
        
        return regulations

    def transform_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform parsed XML data into final JSON structure.
        
        Args:
            parsed_data: Parsed data from XML
            
        Returns:
            Transformed data ready for JSON export
        """
        logger.info("Transforming data...")
        
        json_data = {
            'metadata': {
                'version': '2.0',
                'standard': 'IEC62474',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': IEC62474_CONFIG['base_url'],
                'total_substances': parsed_data['total_substances'],
                'regulations': parsed_data.get('regulations', []),
                'description': 'IEC62474 Declarable Substances List integrating RoHS, REACH, GADSL, Conflict Minerals, and other global regulations'
            },
            'substances': parsed_data['substances'],
            'substance_groups': parsed_data['substance_groups']
        }
        
        return json_data

    def load_to_json(self, json_data: Dict[str, Any]) -> str:
        """
        Save transformed data to JSON file (fixed filename, always latest).
        
        Args:
            json_data: Data to save
            
        Returns:
            Path to the saved JSON file
        """
        output_file = self.json_dir / IEC62474_CONFIG['json_filename']
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON data saved to: {output_file}")
            logger.info(f"Total substances: {json_data['metadata']['total_substances']}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")
            raise

    def validate_data(self, json_data: Dict[str, Any]) -> bool:
        """
        Validate the JSON data structure.
        
        Args:
            json_data: JSON data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check metadata
            if 'metadata' not in json_data:
                logger.error("Missing metadata section")
                return False
            
            metadata = json_data['metadata']
            required_meta_fields = ['version', 'standard', 'last_updated', 'source', 'total_substances']
            for field in required_meta_fields:
                if field not in metadata:
                    logger.error(f"Missing metadata field: {field}")
                    return False
            
            # Check substances
            if 'substances' not in json_data:
                logger.error("Missing substances section")
                return False
            
            substances = json_data['substances']
            if not isinstance(substances, list):
                logger.error("Substances should be a list")
                return False
            
            # Check each substance has required fields
            for i, substance in enumerate(substances):
                if 'name' not in substance:
                    logger.error(f"Substance at index {i} missing 'name' field")
                    return False
            
            logger.info("Data validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Data validation error: {e}")
            return False

    def run_etl(self, skip_download: bool = False, xml_file: str = None) -> str:
        """
        Run the complete ETL process.
        
        Args:
            skip_download: Skip downloading and use existing XML file
            xml_file: Path to existing XML file (if skip_download is True)
            
        Returns:
            Path to the created JSON file
        """
        logger.info("Starting IEC62474 ETL process...")
        
        # Extract
        if skip_download:
            if xml_file and Path(xml_file).exists():
                xml_path = xml_file
                logger.info(f"Using existing XML file: {xml_path}")
            else:
                # Look for existing XML in downloads directory
                xml_files = list(self.download_dir.glob('*.xml'))
                if xml_files:
                    xml_path = str(sorted(xml_files, key=lambda p: p.stat().st_mtime, reverse=True)[0])
                    logger.info(f"Using most recent XML file: {xml_path}")
                else:
                    raise FileNotFoundError("No existing XML file found. Run without --skip-download first.")
        else:
            xml_path = self.download_xml()
        
        # Parse XML
        parsed_data = self.parse_xml(xml_path)
        
        # Transform
        json_data = self.transform_data(parsed_data)
        
        # Validate
        if not self.validate_data(json_data):
            raise ValueError("Data validation failed")
        
        # Load
        output_path = self.load_to_json(json_data)
        
        logger.info("ETL process completed successfully")
        logger.info(f"Output file: {output_path}")
        
        return output_path


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description='IEC62474 Declarable Substances ETL Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and process IEC62474 data
  python iec62474_etl.py
  
  # Use existing XML file
  python iec62474_etl.py --skip-download
  
  # Use specific XML file
  python iec62474_etl.py --skip-download --xml-file path/to/file.xml
        """
    )
    
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip downloading XML and use existing file'
    )
    
    parser.add_argument(
        '--xml-file',
        help='Path to existing XML file (used with --skip-download)'
    )
    
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Directory for data files (default: data)'
    )
    
    args = parser.parse_args()
    
    try:
        processor = IEC62474EtlProcessor(data_dir=args.data_dir)
        output_file = processor.run_etl(
            skip_download=args.skip_download,
            xml_file=args.xml_file
        )
        
        print(f"\n{'='*60}")
        print(f"ETL Process Completed Successfully!")
        print(f"{'='*60}")
        print(f"Output file: {output_file}")
        print(f"\nThe JSON file always contains the latest data.")
        print(f"Previous version has been replaced.")
        print(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"ETL process failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

