# AML Research Tool 🧬

A comprehensive research tool for analyzing Acute Myeloid Leukemia (AML) and TP53 mutation literature using AI-powered analysis and data visualization.

## 🌟 Features

- **📚 PubMed Integration**: Automated paper collection using NCBI E-utilities API
- **🤖 AI Analysis**: Grok-2 powered paper analysis and key findings extraction
- **🌍 Multi-language Summaries**: Generate research summaries in English, French, and Russian
- **🔍 Advanced Search**: Filter papers by year, type, keywords, and more
- **📊 Data Visualization**: Interactive charts and analytics dashboard
- **📁 Export Capabilities**: CSV data export and PDF summary reports
- **⚡ Real-time Updates**: Incremental database updates with new publications

## 🚀 Live Demo

![Dashboard Screenshot](https://via.placeholder.com/800x400?text=AML+Research+Tool+Dashboard)

## 📋 Prerequisites

- Python 3.8+
- XAI API Key (for Grok-2 AI analysis)
- Git

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/romaxnova/amlr.git
   cd amlr
   ```

2. **Create virtual environment**
   ```bash
   python -m venv amlr
   source amlr/bin/activate  # On Windows: amlr\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your XAI_API_KEY
   ```

5. **Initialize the database**
   ```bash
   python -c "from src.database import DatabaseManager; DatabaseManager().init_db()"
   ```

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
XAI_API_KEY=your_xai_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

## 🏃‍♂️ Quick Start

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Access the web interface**
   - Open your browser to `http://localhost:5000`
   - Use the dashboard to explore existing data or update the database

3. **First-time setup**
   - Click "Update Research" → "Full Rebuild" to populate the database
   - This will fetch ~360 papers and process them with AI analysis (10-15 minutes)

## 📖 Usage

### Dashboard
- View research statistics and trends
- Interactive charts showing papers by year
- Quick access to all features

### Summary Generation
- Generate comprehensive AI-powered summaries
- Multi-language support (EN/FR/RU)
- Export summaries as PDF reports

### Database Browser
- Search through all papers
- Filter by year, article type, keywords
- View detailed paper information

### Analytics
- Research trend analysis
- Publication patterns over time
- Key findings visualization

### Data Export
- Export complete database as CSV
- Generate PDF summary reports
- Bulk data analysis capabilities

## 🏗️ Architecture

```
amlr/
├── app.py                 # Flask web application
├── src/
│   ├── database.py        # SQLite database management
│   ├── pubmed_scraper.py  # NCBI E-utilities API integration
│   ├── ai_analyzer.py     # Grok-2 AI analysis
│   └── export_manager.py  # Data export utilities
├── templates/             # HTML templates
├── static/               # CSS, JS, images
└── data/                 # Database and exports
```

## 🔧 API Endpoints

- `GET /` - Dashboard
- `GET /browse` - Database browser
- `GET /generate_summary` - Summary generation page
- `POST /api/generate_summary` - Generate AI summary
- `GET /api/export_csv` - Export database as CSV
- `POST /update_research` - Update paper database

## 🧪 Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Formatting
```bash
black src/ app.py
flake8 src/ app.py
```

### Database Schema
The SQLite database includes tables for:
- `papers` - Research paper metadata and content
- `settings` - Application configuration
- `updates` - Update history tracking

## 🔌 API Integration

### NCBI E-utilities
- Uses official PubMed API for reliable data access
- Implements rate limiting (3 requests/second)
- Retrieval of full abstracts and metadata

### XAI Grok-2
- AI-powered analysis of research papers
- Key findings extraction
- Multi-language summary generation

## 📊 Data Sources

- **PubMed**: NCBI's database of biomedical literature
- **Search Query**: `(acute myeloid leukemia[Title/Abstract] OR AML[Title/Abstract]) AND (TP53[Title/Abstract] OR p53[Title/Abstract])`
- **Date Range**: Last 12 months (configurable)
- **Paper Limit**: ~360 papers (adjustable)

## 🛡️ Security

- Environment variables for sensitive data
- Input validation and sanitization
- Rate limiting for API calls
- Secure file handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. Check the [Issues](https://github.com/romaxnova/amlr/issues) page
2. Review the troubleshooting section below
3. Create a new issue with detailed information

### Common Issues

**"AI summary generation unavailable"**
- Verify your `XAI_API_KEY` is correctly set in `.env`
- Check your XAI API quota and billing

**"No papers found"**
- Run the initial database population: "Update Research" → "Full Rebuild"
- Check internet connectivity for PubMed API access

**Database errors**
- Ensure SQLite permissions in the `data/` directory
- Try deleting `data/research.db` and re-initializing

## 🎯 Roadmap

- [ ] Advanced filtering options
- [ ] User authentication system
- [ ] Citation management integration
- [ ] Collaborative features
- [ ] REST API documentation
- [ ] Docker deployment
- [ ] Cloud database support

## 📈 Statistics

Current database contains:
- **356 research papers**
- **Papers from 2024-2025**
- **Full abstract analysis**
- **AI-generated insights**

## 🙏 Acknowledgments

- [NCBI](https://www.ncbi.nlm.nih.gov/) for PubMed API access
- [XAI](https://x.ai/) for Grok-2 AI capabilities
- [Bootstrap](https://getbootstrap.com/) for UI components
- [Plotly](https://plotly.com/) for data visualization

---

**Built with ❤️ for the scientific research community**
