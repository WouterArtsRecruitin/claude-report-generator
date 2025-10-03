# CLAUDE REPORT GENERATOR - CSV + ZAPIER SETUP
## Simplified versie zonder Google API complexiteit

---

## 🎯 WAAROM DEZE AANPAK?

**✅ Voordelen:**
- Geen Google Cloud setup nodig
- Geen service accounts of API credentials
- Upload CSV direct naar Google Sheets (drag & drop)
- Zapier leest Google Sheets automatisch
- Veel simpeler te onderhouden

**📊 Workflow:**
1. Upload `prospects_sample.csv` → Google Sheets
2. Upload `market_data_sample.csv` → Google Sheets  
3. Zapier triggers Claude script via webhook
4. Script genereert markdown reports
5. Reports opgeslagen als bestanden
6. Zapier kan bestanden emailen/uploaden

---

## 📋 STAP 1: CSV BESTANDEN UPLOADEN

### A) Prospects Sheet
1. Ga naar Google Sheets
2. **File → Import → Upload**
3. Selecteer `prospects_sample.csv`
4. **Import location:** Create new spreadsheet
5. Naam: "Arts Recruitin Prospects"
6. Share link kopiëren voor Zapier

**Kolommen in CSV:**
- company_name, industry, company_size, location
- job_title, function_area, seniority  
- salary_min, salary_max, days_open
- contact_name, contact_title, email
- tier_score (voor ranking)

### B) Market Data Sheet  
1. Nieuwe spreadsheet maken
2. Upload `market_data_sample.csv`
3. Naam: "Nederlandse Job Market Data"
4. Share link kopiëren

**Kolommen in CSV:**
- sector, average_salary, open_positions
- growth_percentage, shortage_level
- top_skills, market_trend

---

## 📋 STAP 2: SCRIPT DEPLOYMENT (RENDER.COM)

### A) Simplified Requirements
```bash
# Alleen deze packages nodig:
pip install anthropic flask pandas requests jinja2 markdown2
```

### B) Deploy naar Render
1. Upload deze bestanden naar GitHub:
   - `claude_csv_report_generator.py`
   - `requirements_simple.txt`
   - `.env_simple` (renamed to `.env`)
   - `prospects_sample.csv`
   - `market_data_sample.csv`

2. **Render.com deployment:**
   - **Build Command:** `pip install -r requirements_simple.txt`
   - **Start Command:** `python claude_csv_report_generator.py`

3. **Environment Variables:**
   ```
   CLAUDE_API_KEY=sk-ant-your-key-here
   PORT=5000
   ```

### C) Test Deployment
```bash
# Health check
curl https://your-app.onrender.com/health

# Test single report
curl -X POST "https://your-app.onrender.com/weekly?prospects=1"
```

---

## 📋 STAP 3: ZAPIER INTEGRATIE

### A) Weekly Reports Zap

**Trigger:** Schedule (Monday 12:00)

**Action 1:** Google Sheets - Get Many Rows
- **Spreadsheet:** Arts Recruitin Prospects
- **Worksheet:** Sheet1  
- **Range:** A2:O11 (top 10 prospects)

**Action 2:** Webhooks by Zapier
- **Method:** POST
- **URL:** `https://your-app.onrender.com/weekly`
- **Query Params:** `prospects=10`

**Action 3:** Email by Zapier
- **To:** team@artsrecruitin.nl
- **Subject:** Weekly Recruitment Reports Generated
- **Body:** 
  ```
  Beste team,
  
  De weekly recruitment reports zijn gegenereerd:
  {{2.count}} rapporten aangemaakt
  
  Status: {{2.success}}
  
  Check de generated_reports folder voor de bestanden.
  ```

### B) Monthly Reports Zap

**Trigger:** Schedule (Last Friday, 18:00)
```
0 18 * * 5
```

**Action 1:** Webhooks by Zapier  
- **URL:** `https://your-app.onrender.com/monthly`
- **Query Params:** `sector=all`

**Action 2:** Email Notification
- **Subject:** Monthly Sector Report Available
- **Body:** Report pad: {{1.report}}

---

## 📋 STAP 4: DATA UPDATE WORKFLOW

### A) Update Prospects (Weekly)
1. **Download current Google Sheet** as CSV
2. **Update data** (nieuwe prospects, tier scores, etc.)
3. **Re-upload** naar Google Sheets
4. Zapier gebruikt automatisch nieuwe data

### B) Update Market Data (Monthly)  
1. **Download current Market Data sheet**
2. **Update cijfers** (salary trends, open positions, growth %)
3. **Re-upload** naar Google Sheets

### C) Automated Updates (Advanced)
**Zapier kan ook Google Sheets updaten:**
- **Trigger:** Webhook van andere systems
- **Action:** Google Sheets - Update Row
- Bijvoorbeeld: Pipedrive changes → Update prospect tier_score

---

## 📊 STAP 5: RAPPORTAGES & OUTPUT

### A) Generated Reports
**Script maakt markdown bestanden:**
```
./generated_reports/
├── Weekly_Report_ASML_20251003.md
├── Weekly_Report_Philips_20251003.md
├── Monthly_Report_all_202510.md
└── report_analytics.csv
```

### B) Report Analytics CSV
**Automatisch gegenereerd:**
- timestamp, report_type, company_name
- file_path, success, processing_time

**Upload naar Google Sheets voor dashboard:**
1. Download `report_analytics.csv` van server
2. Upload naar nieuwe sheet "Report Analytics"
3. Maak charts van success rates, processing times

### C) Email Delivery (via Zapier)
**Optie 1: Send as attachment**
- Zapier kan bestanden van server downloaden
- Attach aan email via Gmail/Outlook action

**Optie 2: Send download links**  
- Host bestanden op server
- Email links naar team

---

## 💰 COST BREAKDOWN

### Simplified Approach:
```
Render.com: €7/maand (hosting)
Claude API: ~€18.50/maand (based on usage)
Zapier: €73/maand (je hebt al Premium)
Google Sheets: Gratis
Total: €98.50/maand

vs Complexe Google API approach: €125+/maand
Savings: €25+/maand door geen extra APIs
```

**Tijd besparingen:**
- Setup tijd: 2 uur vs 8 uur (Google API setup)
- Maintenance: 1 uur/maand vs 4 uur/maand
- Data updates: 10 min vs 30 min

---

## 🚀 DEPLOYMENT CHECKLIST

**Pre-deployment:**
- [ ] CSV templates gecreëerd
- [ ] Google Sheets uploads gedaan
- [ ] Claude API key getest
- [ ] Script getest lokaal

**Deployment:**
- [ ] GitHub repo aangemaakt met bestanden
- [ ] Render.com deployment successful  
- [ ] Environment variables geconfigureerd
- [ ] Health check endpoint werkt

**Zapier Setup:**
- [ ] Weekly reports Zap geconfigureerd
- [ ] Monthly reports Zap geconfigureerd  
- [ ] Test runs successful
- [ ] Email notifications werkend
- [ ] Error handling getest

**Go Live:**
- [ ] Schedules enabled
- [ ] Team getraind op CSV updates
- [ ] Monitoring dashboard setup
- [ ] Backup procedures gedocumenteerd

---

## 🔧 TROUBLESHOOTING

### **CSV Related Issues:**

**Encoding problemen:**
```python
# In script, force UTF-8:
df = pd.read_csv(file_path, encoding='utf-8')
```

**Missing columns:**
```python
# Script checkt required columns:
required_cols = ['company_name', 'industry', 'tier_score']
if not all(col in df.columns for col in required_cols):
    raise ValueError(f"Missing required columns")
```

### **Zapier Integration Issues:**

**Webhook timeouts:**
- Reports generation kan lang duren
- Gebruik async processing of split in batches

**File access voor email attachments:**
```python
# Expose files via HTTP endpoint:
@app.route('/download/<filename>')
def download_file(filename):
    return send_file(f'./generated_reports/{filename}')
```

---

## 📞 QUICK START (30 MIN)

**1. Download & Test (10 min)**
```bash
# Download files
# Set CLAUDE_API_KEY in .env_simple
pip install -r requirements_simple.txt
python claude_csv_report_generator.py test
```

**2. Upload CSVs to Google Sheets (5 min)**
- Upload prospects_sample.csv
- Upload market_data_sample.csv  
- Copy sheet URLs

**3. Deploy to Render (10 min)**
- Push to GitHub
- Connect Render
- Set environment variables
- Deploy

**4. Test Zapier Webhook (5 min)**
```bash
curl -X POST "https://your-app.onrender.com/weekly?prospects=2"
```

**✅ KLAAR!**

Je hebt nu een volledig werkend systeem zonder complexe Google API setup. Veel makkelijker te onderhouden en debuggen!

**Next:** Scale naar production met echte prospect data