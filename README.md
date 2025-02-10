# NSTAFF Episode Scraper

## Overview
This script scrapes the "No Such Thing As A Fish" episode list and updates a MySQL database with new episodes.

## Setup
1. Clone this repository:
    `git clone https://github.com/yourusername/your-repo.git cd your-repo`

2. Install dependencies:
    `pip install -r requirements.txt`

3. Run manually:
    `python scraper/scraper.py`

4. Deploy to **Railway** and schedule as a cron job.

## Railway Setup
- Deploy this repo on **Railway**.
- Add a **scheduled task**:
    `0 * * * * python scraper/scraper.py`
    This runs every hour.
