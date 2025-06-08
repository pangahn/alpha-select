# Alpha Select

Alpha Select is a Python-based web application for analyzing and visualizing the performance of mutual funds. It provides detailed fund return statistics, including total, average, weekly, and annualized returns, as well as historical net worth data. This tool is designed for investors and financial analysts who need quick insights into fund performance metrics.

## Experience Online

Try it here: [https://alpha-select.vercel.app/](https://alpha-select.vercel.app/)

## Features

- Fetches fund data using AkShare.
- Calculates and displays fund returns, weekly and annualized statistics.
- Provides a web interface built with FastAPI and Jinja2 templates.
- REST API endpoint for programmatic access to fund return data.

## Requirements

- Python 3.8+
- uv (Python package manager)
- Node.js and npm (for Vercel deployment)

## Installation

```bash
# Clone the repository
git clone git@github.com:pangahn/alpha-select.git
cd alpha-select

# Install dependencies
uv sync
```

## Configuration

No additional configuration is required for basic usage. The application uses default settings that work out of the box.

## Usage

1. **Start the web server:**
   ```bash
   python src/main.py
   ```
   The app will be available at [http://localhost:8000](http://localhost:8000).

2. **Access the API:**
   - Get fund returns:
     ```
     GET /api/fund/{fund_code}?investment_amount=100000
     ```

## Deploy to Vercel

```bash
# Install Vercel CLI
sudo npm i -g vercel

# Login to your Vercel account
vercel login

# Test locally
vercel dev

# Deploy to production
vercel deploy
```

## Development

### Setting Up Development Environment

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
uv sync -e dev
```

## License

MIT License

---

> **Note:** This project was developed entirely using Windsurf, the agentic AI coding platform.
