# Recipe Grabber

A Python tool that accepts a recipe URL, extracts the core data (ingredients and steps) using JSON-LD, and exports a clean, human-readable file.

## Requirements
- Python 3.12 or above
- Required packages:
  - `requests`
  - `beautifulsoup4`

## Usage
1. Create a venv:

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
**MacOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```


2. Install dependencies:
```bash
pip install -r requirements.txt
```


3. Run the script from the command line:
```bash
python recipe_scraper.py
```