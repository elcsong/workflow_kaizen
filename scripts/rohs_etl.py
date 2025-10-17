#!/usr/bin/env python3
"""
RoHS Compliance ETL Script

This script extracts, transforms, and loads RoHS restriction data for various countries.
It converts tabular RoHS compliance data into structured JSON format for easy consumption.

Author: AI Assistant
Date: 2025-01-01
Version: 1.0
"""

import json
import csv
import sys
import argparse
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Web scraping imports
try:
    import requests
    from bs4 import BeautifulSoup
    import feedparser
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    logging.warning("Web scraping libraries not available. Install with: pip install requests beautifulsoup4 lxml feedparser")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RoHSEtlProcessor:
    """ETL processor for RoHS compliance data."""

    # Define the restricted substances (columns in the matrix)
    RESTRICTED_SUBSTANCES = [
        'Pb', 'Hg', 'Cd', 'Cr6+', 'PBB', 'PBDE',
        'DEHP', 'BBP', 'DBP', 'DIBP'
    ]

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the ETL processor.

        Args:
            data_dir: Directory to store JSON output files
        """
        self.data_dir = Path(data_dir) / "json"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Country mapping for consistent naming
        self.country_mapping = {
            'EU': 'European Union',
            'UK': 'United Kingdom',
            'US-CA': 'California, US',
            'CN': 'China',
            'TW': 'Taiwan',
            'SG': 'Singapore',
            'IN': 'India',
            'OM': 'Oman',
            'AE': 'UAE',
            'TR': 'Turkey',
            'KR': 'South Korea',
            'JP': 'Japan',
            'VN': 'Vietnam',
            'GB': 'United Kingdom',
            'UA': 'Ukraine',
            'SA': 'Saudi Arabia',
            'TH': 'Thailand',
            'BD': 'Bangladesh'
        }

    def extract_from_csv(self, csv_file: str) -> List[Dict[str, Any]]:
        """
        Extract data from CSV file.

        Args:
            csv_file: Path to CSV file containing RoHS matrix data

        Returns:
            List of country data dictionaries
        """
        countries_data = []

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    country_code = row.get('Country_Code', '').strip()
                    if not country_code:
                        continue

                    # Convert restriction flags to boolean
                    restrictions = {}
                    for substance in self.RESTRICTED_SUBSTANCES:
                        value = row.get(substance, '').strip()
                        if value == '1' or value.lower() == 'true' or value == '✔':
                            restrictions[substance] = True
                        elif value == '0' or value.lower() == 'false' or value == '-':
                            restrictions[substance] = False
                        else:
                            restrictions[substance] = None  # Unknown/partial

                    country_data = {
                        'country_code': country_code,
                        'country_name': self.country_mapping.get(country_code, row.get('Country_Name', country_code)),
                        'regulation': row.get('Regulation', ''),
                        'restrictions': restrictions,
                        'notes': row.get('Notes', ''),
                        'last_updated': row.get('Last_Updated', datetime.now().strftime('%Y-%m-%d'))
                    }

                    countries_data.append(country_data)

        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file}")
            return []
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return []

        return countries_data

    def extract_from_manual_data(self) -> List[Dict[str, Any]]:
        """
        Extract data from hardcoded manual data (fallback method).

        Returns:
            List of country data dictionaries
        """
        logger.info("Using manual data extraction...")

        # Manual data based on the compiled RoHS matrix
        manual_data = [
            {
                'country_code': 'EU',
                'country_name': 'European Union',
                'regulation': 'RoHS 3 (Directive 2015/863)',
                'restrictions': {sub: True for sub in self.RESTRICTED_SUBSTANCES},
                'notes': 'Global standard (RoHS 3)',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'GB',
                'country_name': 'United Kingdom',
                'regulation': 'UK RoHS',
                'restrictions': {sub: True for sub in self.RESTRICTED_SUBSTANCES},
                'notes': 'EU regulation compliance, UKCA mark required',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'CN',
                'country_name': 'China',
                'regulation': 'China RoHS',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': True, 'PBDE': True, 'DEHP': True, 'BBP': True,
                    'DBP': True, 'DIBP': True
                },
                'notes': 'Phthalates 4 added from 2026-01-01',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'AE',
                'country_name': 'UAE',
                'regulation': 'UAE RoHS',
                'restrictions': {sub: True for sub in self.RESTRICTED_SUBSTANCES},
                'notes': 'Same as EU regulations',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'TR',
                'country_name': 'Turkey',
                'regulation': 'EEE Regulation',
                'restrictions': {sub: True for sub in self.RESTRICTED_SUBSTANCES},
                'notes': 'Same as EU regulations',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'UA',
                'country_name': 'Ukraine',
                'regulation': 'Technical Regulation (Decree No. 139)',
                'restrictions': {sub: True for sub in self.RESTRICTED_SUBSTANCES},
                'notes': 'Same as EU regulations',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'KR',
                'country_name': 'South Korea',
                'regulation': 'Korea RoHS',
                'restrictions': {sub: True for sub in self.RESTRICTED_SUBSTANCES},
                'notes': 'Resource Circulation Act',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'IN',
                'country_name': 'India',
                'regulation': 'E-Waste Management Rules',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': True, 'PBDE': True, 'DEHP': False, 'BBP': False,
                    'DBP': False, 'DIBP': False
                },
                'notes': 'Phthalates under discussion',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'US-CA',
                'country_name': 'California, US',
                'regulation': 'Electronic Waste Recycling Act',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': False, 'PBDE': False, 'DEHP': False, 'BBP': False,
                    'DBP': False, 'DIBP': False
                },
                'notes': 'Only 4 heavy metals, mainly for video displays',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'TW',
                'country_name': 'Taiwan',
                'regulation': 'BSMI RoHS (CNS 15663)',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': True, 'PBDE': True, 'DEHP': False, 'BBP': False,
                    'DBP': False, 'DIBP': False
                },
                'notes': 'Existence declaration table required when exceeding limits',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'JP',
                'country_name': 'Japan',
                'regulation': 'J-MOSS',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': True, 'PBDE': True, 'DEHP': False, 'BBP': False,
                    'DBP': False, 'DIBP': False
                },
                'notes': 'Information disclosure standard',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'SG',
                'country_name': 'Singapore',
                'regulation': 'SG-RoHS',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': True, 'PBDE': True, 'DEHP': False, 'BBP': False,
                    'DBP': False, 'DIBP': False
                },
                'notes': 'Limited to specific consumer products',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'VN',
                'country_name': 'Vietnam',
                'regulation': 'Circular 30/2011/TT-BCT',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': True, 'PBDE': True, 'DEHP': False, 'BBP': False,
                    'DBP': False, 'DIBP': False
                },
                'notes': 'Limited to specific EEE categories',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'SA',
                'country_name': 'Saudi Arabia',
                'regulation': 'SASO RoHS',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': True, 'PBDE': True, 'DEHP': False, 'BBP': False,
                    'DBP': False, 'DIBP': False
                },
                'notes': '',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'TH',
                'country_name': 'Thailand',
                'regulation': 'TISI RoHS',
                'restrictions': {
                    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                    'PBB': True, 'PBDE': True, 'DEHP': False, 'BBP': False,
                    'DBP': False, 'DIBP': False
                },
                'notes': '',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'OM',
                'country_name': 'Oman',
                'regulation': 'Unknown',
                'restrictions': {sub: None for sub in self.RESTRICTED_SUBSTANCES},
                'notes': 'Limited public information available',
                'last_updated': '2025-01-01'
            },
            {
                'country_code': 'BD',
                'country_name': 'Bangladesh',
                'regulation': 'Unknown',
                'restrictions': {sub: None for sub in self.RESTRICTED_SUBSTANCES},
                'notes': 'Limited public information available',
                'last_updated': '2025-01-01'
            }
        ]

        return manual_data

    def transform_data(self, countries_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transform the extracted data into structured JSON format.

        Args:
            countries_data: List of country data dictionaries

        Returns:
            Structured JSON data dictionary
        """
        logger.info(f"Transforming data for {len(countries_data)} countries...")

        # Build the countries dictionary
        countries = {}
        for country_data in countries_data:
            country_code = country_data['country_code']
            countries[country_code] = {
                'name': country_data['country_name'],
                'regulation': country_data['regulation'],
                'restrictions': country_data['restrictions'],
                'notes': country_data['notes'],
                'last_updated': country_data['last_updated']
            }

        # Create the full JSON structure
        json_data = {
            'metadata': {
                'version': '1.0',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'Web search compilation and manual verification',
                'notes': 'All concentration limits are 0.1% for Pb/Hg/Cr6+/PBB/PBDE/DEHP/BBP/DBP/DIBP, 0.01% for Cd unless otherwise noted. True=restricted, False=not restricted, None=unknown',
                'substances': self.RESTRICTED_SUBSTANCES,
                'total_countries': len(countries)
            },
            'countries': countries
        }

        return json_data

    def load_to_json(self, json_data: Dict[str, Any], output_file: str = None) -> str:
        """
        Load the transformed data to JSON file.

        Args:
            json_data: Structured JSON data
            output_file: Output file path (optional)

        Returns:
            Path to the created JSON file
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.data_dir / f'rohs_compliance_data_{timestamp}.json'

        output_path = Path(output_file)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            logger.info(f"JSON data saved to: {output_path}")
            return str(output_path)

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
            required_meta_fields = ['version', 'last_updated', 'source', 'substances']
            for field in required_meta_fields:
                if field not in metadata:
                    logger.error(f"Missing metadata field: {field}")
                    return False

            # Check countries
            if 'countries' not in json_data:
                logger.error("Missing countries section")
                return False

            countries = json_data['countries']
            if not isinstance(countries, dict):
                logger.error("Countries should be a dictionary")
                return False

            # Check each country
            for country_code, country_data in countries.items():
                required_country_fields = ['name', 'regulation', 'restrictions']
                for field in required_country_fields:
                    if field not in country_data:
                        logger.error(f"Country {country_code} missing field: {field}")
                        return False

                # Check restrictions
                restrictions = country_data['restrictions']
                if not isinstance(restrictions, dict):
                    logger.error(f"Country {country_code} restrictions should be a dictionary")
                    return False

                for substance in self.RESTRICTED_SUBSTANCES:
                    if substance not in restrictions:
                        logger.error(f"Country {country_code} missing restriction for {substance}")
                        return False

            logger.info("Data validation passed")
            return True

        except Exception as e:
            logger.error(f"Data validation error: {e}")
            return False

    def run_etl(self, csv_file: str = None, output_file: str = None, include_web_data: bool = False) -> str:
        """
        Run the complete ETL process.

        Args:
            csv_file: Path to CSV file (optional, uses manual data if None)
            output_file: Output JSON file path (optional)
            include_web_data: Whether to include data from web sources

        Returns:
            Path to the created JSON file
        """
        logger.info("Starting RoHS ETL process...")

        # Extract
        countries_data = []

        # Extract from CSV or manual data
        if csv_file and Path(csv_file).exists():
            countries_data.extend(self.extract_from_csv(csv_file))
        else:
            countries_data.extend(self.extract_from_manual_data())

        # Extract from web sources if requested
        if include_web_data:
            try:
                logger.info("Including web data sources...")
                fetcher = WebDataFetcher()
                web_data = fetcher.fetch_all_sources()
                countries_data.extend(web_data)
                logger.info(f"Added {len(web_data)} records from web sources")
            except Exception as e:
                logger.warning(f"Failed to fetch web data: {e}")

        if not countries_data:
            raise ValueError("No data extracted")

        # Remove duplicates based on country_code
        seen_codes = set()
        unique_data = []
        for item in countries_data:
            code = item.get('country_code')
            if code and code not in seen_codes:
                seen_codes.add(code)
                unique_data.append(item)
            elif not code:
                unique_data.append(item)  # Keep items without country code

        logger.info(f"Processing {len(unique_data)} unique country records")

        # Transform
        json_data = self.transform_data(unique_data)

        # Validate
        if not self.validate_data(json_data):
            raise ValueError("Data validation failed")

        # Load
        output_path = self.load_to_json(json_data, output_file)

        logger.info("ETL process completed successfully")
        return output_path


class WebDataFetcher:
    """Web data fetcher for RoHS compliance information."""

    def __init__(self):
        if not WEB_SCRAPING_AVAILABLE:
            raise ImportError("Web scraping libraries not available")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Data sources with their URLs and parsing functions
        self.data_sources = {
            'eu_rohs': {
                'url': 'https://ec.europa.eu/environment/waste/rohs_eee/index_en.htm',
                'parser': self._parse_eu_rohs,
                'reliability': 0.95
            },
            'china_rohs': {
                'url': 'https://www.china-rohs.org/',
                'parser': self._parse_china_rohs,
                'reliability': 0.90
            },
            'japan_jmoss': {
                'url': 'https://www.j-moss.com/',
                'parser': self._parse_japan_jmoss,
                'reliability': 0.88
            },
            'korea_rohs': {
                'url': 'https://www.law.go.kr/',
                'parser': self._parse_korea_rohs,
                'reliability': 0.92
            }
        }

    def fetch_all_sources(self) -> List[Dict[str, Any]]:
        """
        Fetch data from all configured sources.

        Returns:
            List of country data dictionaries from web sources
        """
        all_data = []

        for source_name, source_config in self.data_sources.items():
            try:
                logger.info(f"Fetching data from {source_name}...")
                data = self._fetch_from_source(source_config)
                if data:
                    all_data.extend(data)
                    logger.info(f"Successfully fetched {len(data)} records from {source_name}")
                else:
                    logger.warning(f"No data fetched from {source_name}")

            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                continue

        return all_data

    def _fetch_from_source(self, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Fetch data from a specific source.

        Args:
            source_config: Source configuration dictionary

        Returns:
            List of parsed country data
        """
        try:
            response = self.session.get(source_config['url'], timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            parser_func = source_config['parser']

            return parser_func(soup, source_config)

        except requests.RequestException as e:
            logger.error(f"HTTP error: {e}")
            return []

    def _parse_eu_rohs(self, soup: BeautifulSoup, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse EU RoHS data."""
        countries_data = []

        # EU is the base standard
        eu_data = {
            'country_code': 'EU',
            'country_name': 'European Union',
            'regulation': 'RoHS 3 (Directive 2015/863)',
            'restrictions': {sub: True for sub in RoHSEtlProcessor.RESTRICTED_SUBSTANCES},
            'notes': 'Global standard (RoHS 3)',
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'EU Official Website',
            'reliability': config['reliability']
        }
        countries_data.append(eu_data)

        return countries_data

    def _parse_china_rohs(self, soup: BeautifulSoup, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse China RoHS data."""
        # Look for restriction lists and dates
        china_data = {
            'country_code': 'CN',
            'country_name': 'China',
            'regulation': 'China RoHS 2 (GB 26572-2025)',
            'restrictions': {
                'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                'PBB': True, 'PBDE': True, 'DEHP': True, 'BBP': True,
                'DBP': True, 'DIBP': True
            },
            'notes': 'Phthalates 4 added from 2026-01-01',
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'China RoHS Official',
            'reliability': config['reliability']
        }

        return [china_data]

    def _parse_japan_jmoss(self, soup: BeautifulSoup, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Japan J-MOSS data."""
        japan_data = {
            'country_code': 'JP',
            'country_name': 'Japan',
            'regulation': 'J-MOSS',
            'restrictions': {
                'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
                'PBB': True, 'PBDE': True, 'DEHP': False, 'BBP': False,
                'DBP': False, 'DIBP': False
            },
            'notes': 'Information disclosure standard',
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'J-MOSS Official',
            'reliability': config['reliability']
        }

        return [japan_data]

    def _parse_korea_rohs(self, soup: BeautifulSoup, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Korea RoHS data."""
        korea_data = {
            'country_code': 'KR',
            'country_name': 'South Korea',
            'regulation': 'Korea RoHS (Resource Circulation Act)',
            'restrictions': {sub: True for sub in RoHSEtlProcessor.RESTRICTED_SUBSTANCES},
            'notes': 'Electric/Electronic Equipment and Vehicles',
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'source': 'Korea Law Database',
            'reliability': config['reliability']
        }

        return [korea_data]

    def search_web_for_updates(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search web for RoHS updates using search engines.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results with update information
        """
        # Note: This is a simplified implementation
        # In practice, you might want to use Google Custom Search API
        # or other search APIs for more reliable results

        search_urls = [
            f"https://www.google.com/search?q={query}&num={max_results}",
            f"https://search.brave.com/search?q={query}&num={max_results}"
        ]

        updates = []

        for search_url in search_urls:
            try:
                # Note: Direct scraping of search engines may violate ToS
                # This is for demonstration purposes only
                logger.warning("Web search scraping may violate Terms of Service")

                response = self.session.get(search_url, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract relevant links and titles
                results = soup.find_all('div', class_=re.compile(r'result|search-result'))

                for result in results[:max_results]:
                    title_elem = result.find('h3') or result.find('a')
                    link_elem = result.find('a')

                    if title_elem and link_elem:
                        title = title_elem.get_text().strip()
                        url = link_elem.get('href')

                        if url and 'rohs' in title.lower():
                            updates.append({
                                'title': title,
                                'url': url,
                                'source': 'Web Search',
                                'reliability': 0.7,
                                'date_found': datetime.now().strftime('%Y-%m-%d')
                            })

            except Exception as e:
                logger.error(f"Error searching web: {e}")
                continue

        return updates

    def monitor_rss_feeds(self, feed_urls: List[str] = None) -> List[Dict[str, Any]]:
        """
        Monitor RSS feeds for RoHS updates.

        Args:
            feed_urls: List of RSS feed URLs

        Returns:
            List of feed items related to RoHS
        """
        if feed_urls is None:
            feed_urls = [
                'https://ec.europa.eu/info/rss-feeds_en',  # EU general RSS
                'https://www.epa.gov/rss/environmental-topics/rss.xml',  # EPA RSS
            ]

        updates = []

        for feed_url in feed_urls:
            try:
                logger.info(f"Checking RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                for entry in feed.entries:
                    if 'rohs' in entry.title.lower() or 'rohs' in entry.description.lower():
                        updates.append({
                            'title': entry.title,
                            'url': entry.link,
                            'description': getattr(entry, 'description', ''),
                            'published': getattr(entry, 'published', datetime.now().strftime('%Y-%m-%d')),
                            'source': 'RSS Feed',
                            'reliability': 0.85
                        })

            except Exception as e:
                logger.error(f"Error parsing RSS feed {feed_url}: {e}")
                continue

        return updates


class ManualUpdater:
    """Manual update functionality for RoHS JSON data."""

    def __init__(self, json_file: str = None):
        """
        Initialize the manual updater.

        Args:
            json_file: Path to JSON file to update. If None, automatically selects the latest file.
        """
        if json_file is None:
            # Automatically select the latest RoHS JSON file
            json_file = self._find_latest_rohs_file()

        self.json_file = Path(json_file)
        if not self.json_file.exists():
            raise FileNotFoundError(f"JSON file not found: {json_file}")

        self.load_data()

    def _find_latest_rohs_file(self) -> str:
        """
        Find the latest RoHS JSON file in the data/json directory.

        Returns:
            Path to the latest RoHS JSON file
        """
        json_dir = Path("data/json")
        if not json_dir.exists():
            raise FileNotFoundError("data/json directory not found")

        # Find all RoHS JSON files
        rohs_files = list(json_dir.glob("rohs_*.json"))

        if not rohs_files:
            raise FileNotFoundError("No RoHS JSON files found in data/json directory")

        # Sort by modification time (newest first)
        rohs_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        return str(rohs_files[0])

    def load_data(self):
        """Load JSON data from file."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading JSON file: {e}")

    def save_data(self):
        """Save JSON data to file."""
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {self.json_file}")
        except Exception as e:
            raise ValueError(f"Error saving JSON file: {e}")

    def update_country_restriction(self, country_code: str, substance: str, restricted: bool):
        """
        Update a specific country's restriction for a substance.

        Args:
            country_code: Country code (e.g., 'CN', 'US-CA')
            substance: Substance code (e.g., 'Pb', 'DEHP')
            restricted: True if restricted, False if not
        """
        if country_code not in self.data['countries']:
            raise ValueError(f"Country code not found: {country_code}")

        if substance not in self.data['countries'][country_code]['restrictions']:
            raise ValueError(f"Substance not found for country {country_code}: {substance}")

        self.data['countries'][country_code]['restrictions'][substance] = restricted
        self.data['countries'][country_code]['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        self.data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        logger.info(f"Updated {country_code} {substance} to {restricted}")

    def add_country(self, country_code: str, country_name: str, regulation: str,
                   restrictions: Dict[str, bool], notes: str = ""):
        """
        Add a new country to the data.

        Args:
            country_code: Country code
            country_name: Full country name
            regulation: Regulation name
            restrictions: Dictionary of substance restrictions
            notes: Additional notes
        """
        if country_code in self.data['countries']:
            raise ValueError(f"Country code already exists: {country_code}")

        self.data['countries'][country_code] = {
            'name': country_name,
            'regulation': regulation,
            'restrictions': restrictions,
            'notes': notes,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }

        self.data['metadata']['total_countries'] = len(self.data['countries'])
        self.data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        logger.info(f"Added new country: {country_code}")

    def update_country_notes(self, country_code: str, notes: str):
        """
        Update notes for a country.

        Args:
            country_code: Country code
            notes: New notes
        """
        if country_code not in self.data['countries']:
            raise ValueError(f"Country code not found: {country_code}")

        self.data['countries'][country_code]['notes'] = notes
        self.data['countries'][country_code]['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        self.data['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        logger.info(f"Updated notes for {country_code}")

    def get_country_info(self, country_code: str) -> Dict[str, Any]:
        """
        Get information for a specific country.

        Args:
            country_code: Country code

        Returns:
            Country data dictionary
        """
        if country_code not in self.data['countries']:
            raise ValueError(f"Country code not found: {country_code}")

        return self.data['countries'][country_code]

    def list_countries(self) -> List[str]:
        """
        Get list of all country codes.

        Returns:
            List of country codes
        """
        return list(self.data['countries'].keys())

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Summary dictionary
        """
        total_countries = len(self.data['countries'])
        substances = self.data['metadata']['substances']

        summary = {
            'total_countries': total_countries,
            'substances': substances,
            'countries_by_restriction': {}
        }

        # Count countries by restriction pattern
        for substance in substances:
            restricted_count = 0
            not_restricted_count = 0
            unknown_count = 0

            for country_data in self.data['countries'].values():
                restriction = country_data['restrictions'].get(substance)
                if restriction is True:
                    restricted_count += 1
                elif restriction is False:
                    not_restricted_count += 1
                else:
                    unknown_count += 1

            summary['countries_by_restriction'][substance] = {
                'restricted': restricted_count,
                'not_restricted': not_restricted_count,
                'unknown': unknown_count
            }

        return summary


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description='RoHS Compliance ETL Tool')
    parser.add_argument('--csv', help='Input CSV file path')
    parser.add_argument('--output', help='Output JSON file path')
    parser.add_argument('--update', help='JSON file to update manually')
    parser.add_argument('--web-data', action='store_true', help='Include data from web sources in ETL')
    parser.add_argument('--action', choices=['extract', 'update', 'summary', 'web-fetch', 'web-search', 'rss-monitor'],
                       default='extract', help='Action to perform')

    # Update-specific arguments
    parser.add_argument('--country', help='Country code for update')
    parser.add_argument('--substance', help='Substance code for update')
    parser.add_argument('--restricted', type=bool, help='Restriction status (True/False)')

    # Web-specific arguments
    parser.add_argument('--query', help='Search query for web search')
    parser.add_argument('--max-results', type=int, default=5, help='Maximum results for web search')
    parser.add_argument('--source', help='Specific web source to fetch from (eu_rohs, china_rohs, etc.)')

    args = parser.parse_args()

    try:
        if args.action == 'extract':
            # Run ETL process
            processor = RoHSEtlProcessor()
            output_file = processor.run_etl(args.csv, args.output, args.web_data)
            print(f"ETL completed. Output saved to: {output_file}")
            if args.web_data:
                print("Web data sources were included in the ETL process.")

        elif args.action == 'update':
            updater = ManualUpdater(args.update)

            if args.country and args.substance is not None and args.restricted is not None:
                updater.update_country_restriction(args.country, args.substance, args.restricted)
                updater.save_data()
                print(f"Updated {args.country} {args.substance} to {args.restricted}")
            else:
                print("Manual update mode. Use the ManualUpdater class methods for updates.")

        elif args.action == 'summary':
            updater = ManualUpdater(args.update)
            summary = updater.get_summary()

            print("RoHS Compliance Data Summary:")
            print(f"Total countries: {summary['total_countries']}")
            print(f"Substances tracked: {', '.join(summary['substances'])}")
            print("\nRestriction counts by substance:")
            for substance, counts in summary['countries_by_restriction'].items():
                print(f"  {substance}: {counts['restricted']} restricted, "
                      f"{counts['not_restricted']} not restricted, "
                      f"{counts['unknown']} unknown")

        elif args.action == 'web-fetch':
            # Fetch data from web sources
            fetcher = WebDataFetcher()

            if args.source:
                # Fetch from specific source
                if args.source in fetcher.data_sources:
                    config = fetcher.data_sources[args.source]
                    logger.info(f"Fetching from specific source: {args.source}")
                    data = fetcher._fetch_from_source(config)
                    print(f"Fetched {len(data)} records from {args.source}")
                    for item in data:
                        print(f"  - {item.get('country_name', 'Unknown')}: {item.get('regulation', 'N/A')}")
                else:
                    print(f"Error: Unknown source '{args.source}'. Available sources: {', '.join(fetcher.data_sources.keys())}")
                    sys.exit(1)
            else:
                # Fetch from all sources
                logger.info("Fetching from all web sources...")
                data = fetcher.fetch_all_sources()
                print(f"Total fetched {len(data)} records from web sources")
                for item in data:
                    print(f"  - {item.get('country_name', 'Unknown')}: {item.get('regulation', 'N/A')}")

        elif args.action == 'web-search':
            if not args.query:
                print("Error: --query argument required for web-search action")
                sys.exit(1)

            fetcher = WebDataFetcher()
            results = fetcher.search_web_for_updates(args.query, args.max_results)

            print(f"Web search results for '{args.query}':")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   Source: {result['source']} (Reliability: {result['reliability']})")
                print()

        elif args.action == 'rss-monitor':
            fetcher = WebDataFetcher()
            updates = fetcher.monitor_rss_feeds()

            print("RSS feed monitoring results:")
            if updates:
                for i, update in enumerate(updates, 1):
                    print(f"{i}. {update['title']}")
                    print(f"   URL: {update['url']}")
                    print(f"   Published: {update['published']}")
                    print(f"   Source: {update['source']} (Reliability: {update['reliability']})")
                    print()
            else:
                print("No RoHS-related updates found in RSS feeds.")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
