# LinkedIn Jobs Scraper

A Python script for automatically scraping job listings from LinkedIn. Collects job listings based on specified search criteria (job title, location) and saves them in JSON or CSV format.

## Features

- Automatically scrapes LinkedIn job listings based on specified search criteria
- Two different operation modes: with or without accessing the detail panel
- Output in JSON and CSV formats
- Customizable number of job listings to collect (default: 50)
- Option for headless (background) or normal browser operation

## Requirements

- Python 3.6+
- Chrome browser
- ChromeDriver
- Selenium and other required packages

```bash
pip install selenium webdriver-manager
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Linkedin-Jobs-Scraper.git
cd Linkedin-Jobs-Scraper
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Install ChromeDriver (for macOS):
```bash
brew install --cask chromedriver
xattr -d com.apple.quarantine $(which chromedriver)
```

## Usage

### Basic Usage

```bash
python Linkedin_jobs_scraper.py --job-title "data scientist" --location "London"
```

### Fast Mode (Skip Detail Panel)

```bash
python Linkedin_jobs_scraper.py --job-title "data scientist" --location "London" --skip-details
```

### All Parameters

```bash
python Linkedin_jobs_scraper.py --job-title "data scientist" \
                           --location "London" \
                           --max-jobs 100 \
                           --max-scrolls 20 \
                           --output-format json \
                           --output-file "my_jobs_data" \
                           --headless \
                           --username "YourName" \
                           --skip-details
```

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| `--job-title` | Job title to search for | (Required) |
| `--location` | Location to search in | (Required) |
| `--max-jobs` | Maximum number of job listings to collect | 50 |
| `--max-scrolls` | Maximum number of scrolls to perform | 20 |
| `--output-format` | Output format (json, csv, both) | json |
| `--output-file` | Output file name (without extension) | (Automatically generated) |
| `--headless` | Run browser in background | False |
| `--username` | Username for attribution | None |
| `--skip-details` | Collect basic information without clicking the detail panel | False |

## Example Output

```json
[
  {
    "id": "3574136587",
    "title": "Data Scientist",
    "company": "Example Company",
    "location": "London, UK",
    "job_type": "Full-time",
    "description": "We are looking for a Data Scientist to join our team...",
    "apply_link": "https://www.linkedin.com/jobs/view/3574136587",
    "date_posted": "2 days ago",
    "scraped_date": "2023-08-15T14:30:45.123456",
    "source": "LinkedIn Jobs",
    "attribution": "Collected via LinkedIn Jobs scraper"
  }
]
```

## Notes

- LinkedIn's structure may change over time, so if the script doesn't work, please open an issue
- LinkedIn may take various measures to prevent automated scraping. Avoid excessive use
- This script should be used for educational and personal purposes only

## License

MIT 