# Claude Report Generator - CSV + Zapier

Automated recruitment report generator that works with CSV files and Zapier webhooks.

## Quick Deploy to Render.com

1. **Fork this repository**
2. **Connect to Render.com:**
   - New → Web Service
   - Connect GitHub repo
   - Build command: `pip install -r requirements_simple.txt`
   - Start command: `python claude_csv_report_generator.py`

3. **Environment Variables:**
   ```
   CLAUDE_API_KEY=sk-ant-your-key-here
   PORT=5000
   ```

4. **Deploy!**

## API Endpoints

- `GET /health` - Health check
- `POST /weekly?prospects=10` - Generate weekly reports
- `POST /monthly?sector=all` - Generate monthly reports

## Files

- `claude_csv_report_generator.py` - Main script
- `prospects_sample.csv` - Sample prospects data
- `market_data_sample.csv` - Sample market data
- `CSV_ZAPIER_SETUP_GUIDE.md` - Complete setup instructions

## Usage

Upload CSV files to Google Sheets, then use Zapier to trigger webhooks.

See `CSV_ZAPIER_SETUP_GUIDE.md` for complete instructions.