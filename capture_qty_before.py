"""Capture the BEFORE state of the log-food quantity label (Improvement 2)."""
import os
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:5000'
USER = 'ncea_tester'
PASSWORD = 'NceaTest123'
os.makedirs('screenshots', exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 900})

    page.goto(f'{BASE}/login')
    page.fill('#username', USER)
    page.fill('#password', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')

    page.goto(f'{BASE}/log-food')
    page.wait_for_load_state('networkidle')
    print('URL:', page.url)
    page.screenshot(path='screenshots/before_quantity_label.png',
                    full_page=True)
    print('Saved screenshots/before_quantity_label.png')
    browser.close()
