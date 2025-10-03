#!/usr/bin/env python3
"""
Arts Recruitin - CSV-Based Report Generator
Simplified version that works with CSV files instead of Google Sheets API

Upload CSV files to Google Sheets manually, then use Zapier to trigger this script
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Third-party imports
try:
    import anthropic
    import pandas as pd
    from flask import Flask, request, jsonify
    import requests
    from jinja2 import Template
    import markdown2
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install anthropic pandas flask requests jinja2 markdown2")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('report_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Config:
    """Simplified configuration for CSV-based approach"""
    
    # API Keys (only Claude needed)
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    
    # CSV file paths (local files)
    PROSPECTS_CSV = os.getenv('PROSPECTS_CSV', './prospects_sample.csv')
    MARKET_DATA_CSV = os.getenv('MARKET_DATA_CSV', './market_data_sample.csv')
    
    # Output directory for generated reports
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './generated_reports')
    
    # Claude model
    CLAUDE_MODEL = 'claude-sonnet-4-20250514'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.CLAUDE_API_KEY:
            logger.error("Missing CLAUDE_API_KEY environment variable")
            logger.info("Get your API key from Claude.ai Pro subscription")
            sys.exit(1)
        
        # Create output directory if it doesn't exist
        Path(cls.OUTPUT_DIR).mkdir(exist_ok=True)
        
        logger.info("Configuration validated successfully")

class CSVDataManager:
    """Manages CSV data files"""
    
    def __init__(self):
        self.prospects_file = Config.PROSPECTS_CSV
        self.market_data_file = Config.MARKET_DATA_CSV
    
    def get_prospects(self, limit: int = 10) -> List[Dict]:
        """Read prospects from CSV file"""
        try:
            df = pd.read_csv(self.prospects_file)
            # Sort by tier_score descending to get top prospects
            df = df.sort_values('tier_score', ascending=False).head(limit)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error reading prospects CSV: {e}")
            return []
    
    def get_market_data(self) -> List[Dict]:
        """Read market data from CSV file"""
        try:
            df = pd.read_csv(self.market_data_file)
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error reading market data CSV: {e}")
            return []
    
    def save_report_metadata(self, report_data: Dict):
        """Save report metadata to CSV for analytics"""
        metadata_file = Path(Config.OUTPUT_DIR) / 'report_analytics.csv'
        
        # Create headers if file doesn't exist
        if not metadata_file.exists():
            with open(metadata_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'report_type', 'company_name', 'file_path', 'success', 'processing_time'])
        
        # Append new record
        with open(metadata_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                report_data.get('type', 'unknown'),
                report_data.get('company_name', ''),
                report_data.get('file_path', ''),
                report_data.get('success', False),
                report_data.get('processing_time', 0)
            ])

class ClaudeClient:
    """Simplified Claude API client"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)
        self.model = Config.CLAUDE_MODEL
    
    def generate_report(self, prompt: str, prospect_data: Dict, market_context: List[Dict]) -> str:
        """Generate report using Claude API"""
        
        # Build context
        context = f"""
PROSPECT DATA:
Company: {prospect_data.get('company_name', 'N/A')}
Industry: {prospect_data.get('industry', 'N/A')}
Size: {prospect_data.get('company_size', 'N/A')}
Location: {prospect_data.get('location', 'N/A')}
Role: {prospect_data.get('job_title', 'N/A')}
Salary Range: €{prospect_data.get('salary_min', 0):,} - €{prospect_data.get('salary_max', 0):,}
Days Open: {prospect_data.get('days_open', 0)}
Contact: {prospect_data.get('contact_name', 'N/A')} ({prospect_data.get('contact_title', 'N/A')})
Tier Score: {prospect_data.get('tier_score', 0)}/100

MARKET CONTEXT:
"""
        
        # Add relevant market data
        for sector in market_context:
            if sector.get('sector') in prospect_data.get('industry', ''):
                context += f"""
Sector: {sector.get('sector')}
Average Salary: €{sector.get('average_salary', 0):,}
Open Positions: {sector.get('open_positions', 0)}
Growth: {sector.get('growth_percentage', 0)}%
Skills in Demand: {sector.get('top_skills', 'N/A')}
Market Trend: {sector.get('market_trend', 'N/A')}
"""
        
        full_prompt = f"{prompt}\n\n{context}"
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": full_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"Error generating report: {e}"

class ReportGenerator:
    """Main report generator class"""
    
    def __init__(self):
        Config.validate()
        self.csv_manager = CSVDataManager()
        self.claude = ClaudeClient()
        self.weekly_prompt = self._load_prompt_template('weekly')
        self.monthly_prompt = self._load_prompt_template('monthly')
    
    def _load_prompt_template(self, report_type: str) -> str:
        """Load prompt template (simplified version)"""
        templates = {
            'weekly': """
Schrijf een professionele Nederlandse recruitment markt analyse voor dit bedrijf.

STRUCTUUR:
1. Executive Summary (2-3 zinnen)
2. Bedrijfsanalyse (positie in de markt)
3. Functie-analyse (specifieke rol details)
4. Marktcontext (salary benchmarks, groei trends)
5. Recruitment strategie aanbevelingen
6. Actie items

Schrijf in professionele maar toegankelijke Nederlandse taal.
Gebruik concrete cijfers en data waar beschikbaar.
Houd het beknopt maar informatief (max 800 woorden).
""",
            'monthly': """
Schrijf een uitgebreide Nederlandse sector analyse rapport.

STRUCTUUR:
1. Sector Overview
2. Markt Trends & Ontwikkelingen
3. Salary Benchmarks
4. Skills Gap Analyse
5. Growth Opportunities
6. Strategic Recommendations
7. Forecast & Outlook

Schrijf een diepgaand rapport van 1500-2000 woorden.
Gebruik alle beschikbare marktdata.
Focus op actionable insights voor recruitment professionals.
"""
        }
        return templates.get(report_type, templates['weekly'])
    
    def generate_weekly_reports(self, prospects_count: int) -> List[str]:
        """Generate weekly reports for top prospects"""
        start_time = datetime.now()
        logger.info(f"Generating weekly reports for top {prospects_count} prospects")
        
        prospects = self.csv_manager.get_prospects(prospects_count)
        market_data = self.csv_manager.get_market_data()
        report_files = []
        
        for i, prospect in enumerate(prospects, 1):
            try:
                logger.info(f"Processing prospect {i}/{len(prospects)}: {prospect.get('company_name')}")
                
                # Generate report content
                report_content = self.claude.generate_report(
                    self.weekly_prompt, 
                    prospect, 
                    market_data
                )
                
                # Save to file
                company_name = prospect.get('company_name', 'Unknown').replace(' ', '_')
                filename = f"Weekly_Report_{company_name}_{datetime.now().strftime('%Y%m%d')}.md"
                file_path = Path(Config.OUTPUT_DIR) / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Weekly Recruitment Report - {prospect.get('company_name')}\n\n")
                    f.write(f"**Generated:** {datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n")
                    f.write(report_content)
                
                report_files.append(str(file_path))
                
                # Save metadata
                self.csv_manager.save_report_metadata({
                    'type': 'weekly',
                    'company_name': prospect.get('company_name'),
                    'file_path': str(file_path),
                    'success': True,
                    'processing_time': (datetime.now() - start_time).total_seconds()
                })
                
                logger.info(f"Report saved: {file_path}")
                
            except Exception as e:
                logger.error(f"Error processing prospect {prospect.get('company_name')}: {e}")
                continue
        
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Generated {len(report_files)} reports in {total_time:.2f} seconds")
        
        return report_files
    
    def generate_monthly_report(self, sector: str = 'all') -> str:
        """Generate monthly sector report"""
        start_time = datetime.now()
        logger.info(f"Generating monthly report for sector: {sector}")
        
        market_data = self.csv_manager.get_market_data()
        prospects = self.csv_manager.get_prospects(50)  # Get more data for sector analysis
        
        # Filter data by sector if specified
        if sector != 'all':
            market_data = [item for item in market_data if sector.lower() in item.get('sector', '').lower()]
            prospects = [item for item in prospects if sector.lower() in item.get('industry', '').lower()]
        
        # Create aggregated context
        context = {
            'sector': sector,
            'total_prospects': len(prospects),
            'market_segments': len(market_data),
            'avg_salary': sum(item.get('average_salary', 0) for item in market_data) // len(market_data) if market_data else 0,
            'total_positions': sum(item.get('open_positions', 0) for item in market_data),
        }
        
        # Generate report
        report_content = self.claude.generate_report(
            self.monthly_prompt,
            context,
            market_data
        )
        
        # Save to file
        filename = f"Monthly_Report_{sector}_{datetime.now().strftime('%Y%m')}.md"
        file_path = Path(Config.OUTPUT_DIR) / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Monthly Sector Report - {sector.title()}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%d-%m-%Y %H:%M')}\n\n")
            f.write(report_content)
        
        # Save metadata
        self.csv_manager.save_report_metadata({
            'type': 'monthly',
            'company_name': f'Sector_{sector}',
            'file_path': str(file_path),
            'success': True,
            'processing_time': (datetime.now() - start_time).total_seconds()
        })
        
        logger.info(f"Monthly report saved: {file_path}")
        return str(file_path)

# Flask API for Zapier
app = Flask(__name__)
generator = None

@app.route('/weekly', methods=['POST', 'GET'])
def weekly_endpoint():
    """Zapier webhook for weekly reports"""
    global generator
    if not generator:
        generator = ReportGenerator()
    
    try:
        prospects = request.args.get('prospects', 10, type=int)
        logger.info(f"API request: weekly reports for {prospects} prospects")
        
        report_files = generator.generate_weekly_reports(prospects)
        
        return jsonify({
            'success': True,
            'reports': report_files,
            'count': len(report_files),
            'message': f'Generated {len(report_files)} weekly reports'
        })
    except Exception as e:
        logger.error(f"API error in weekly endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/monthly', methods=['POST', 'GET'])
def monthly_endpoint():
    """Zapier webhook for monthly reports"""
    global generator
    if not generator:
        generator = ReportGenerator()
    
    try:
        sector = request.args.get('sector', 'all')
        logger.info(f"API request: monthly report for sector {sector}")
        
        report_file = generator.generate_monthly_report(sector)
        
        return jsonify({
            'success': True,
            'report': report_file,
            'message': f'Generated monthly report for {sector}'
        })
    except Exception as e:
        logger.error(f"API error in monthly endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'csv_files': {
            'prospects': os.path.exists(Config.PROSPECTS_CSV),
            'market_data': os.path.exists(Config.MARKET_DATA_CSV)
        }
    })

def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(description='Arts Recruitin CSV Report Generator')
    parser.add_argument('command', choices=['weekly', 'monthly', 'test'])
    parser.add_argument('--prospects', type=int, default=10, help='Number of prospects for weekly reports')
    parser.add_argument('--sector', default='all', help='Sector for monthly reports')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        print("🧪 Testing CSV-based configuration...\n")
        
        # Test CSV files
        if os.path.exists(Config.PROSPECTS_CSV):
            df = pd.read_csv(Config.PROSPECTS_CSV)
            print(f"✅ Prospects CSV: {len(df)} records found")
        else:
            print(f"❌ Prospects CSV not found: {Config.PROSPECTS_CSV}")
        
        if os.path.exists(Config.MARKET_DATA_CSV):
            df = pd.read_csv(Config.MARKET_DATA_CSV)
            print(f"✅ Market Data CSV: {len(df)} sectors found")
        else:
            print(f"❌ Market Data CSV not found: {Config.MARKET_DATA_CSV}")
        
        # Test Claude API
        try:
            generator = ReportGenerator()
            print("✅ Claude API connection: OK")
        except Exception as e:
            print(f"❌ Claude API connection: FAILED - {e}")
        
        print(f"\n✅ Output directory: {Config.OUTPUT_DIR}")
        print("\n✅ All tests completed")
        return
    
    # Execute command
    try:
        generator = ReportGenerator()
        
        if args.command == 'weekly':
            report_files = generator.generate_weekly_reports(args.prospects)
            print(f"\n✅ Generated {len(report_files)} weekly reports:")
            for i, file_path in enumerate(report_files, 1):
                print(f"{i}. {file_path}")
        
        elif args.command == 'monthly':
            report_file = generator.generate_monthly_report(args.sector)
            print(f"\n✅ Monthly report generated:")
            print(f"   {report_file}")
        
        logger.info("Command completed successfully")
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()  # CLI mode
    else:
        # API mode for Zapier
        port = int(os.getenv('PORT', 5000))
        print(f"Starting Flask app on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)