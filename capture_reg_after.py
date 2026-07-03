"""Capture the AFTER state of registration redirect (Improvement 1)."""
import os
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:5000'
os.makedirs('screenshots', exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 900})

    page.goto(f'{BASE}/register')
    page.fill('#username', 'ux_after_reg')
    page.fill('#email', 'ux_after_reg@test.com')
    page.fill('#password', 'UxTest123')
    page.fill('#confirm_password', 'UxTest123')
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')

    print('Landed on URL:', page.url)
    page.screenshot(path='screenshots/after_register_redirect.png',
                    full_page=True)
    print('Saved screenshots/after_register_redirect.png')
    browser.close()
