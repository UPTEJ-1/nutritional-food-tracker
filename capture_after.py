"""
Playwright automation to capture the AFTER (fixed) state.
Uses the same ncea_tester account and the same form.submit() bypass of
the client-side min as Part 1, to prove the server now rejects 0 on its
own. Then submits a valid value and confirms the dashboard loads.
"""
import os
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:5000'
USER = 'ncea_tester'
PASSWORD = 'NceaTest123'

os.makedirs('screenshots', exist_ok=True)


def login(page):
    page.goto(f'{BASE}/login')
    page.fill('#username', USER)
    page.fill('#password', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 900})
    login(page)

    # 1) Submit daily_calories = 0, bypassing the client-side min again
    page.goto(f'{BASE}/goals')
    page.fill('#daily_calories', '0')
    page.fill('#daily_protein', '150')
    page.fill('#daily_carbs', '250')
    page.fill('#daily_fats', '65')
    page.evaluate("document.querySelector('form.goals-form').submit()")
    page.wait_for_load_state('networkidle')

    print('After invalid submit -> URL:', page.url)
    print('Flash message present:',
          'must be at least 500' in page.content())
    page.screenshot(path='screenshots/after_validation_message.png',
                    full_page=True)
    print('Saved screenshots/after_validation_message.png')

    # 2) Submit a valid value (2500) and confirm the dashboard loads
    page.goto(f'{BASE}/goals')
    page.fill('#daily_calories', '2500')
    page.fill('#daily_protein', '150')
    page.fill('#daily_carbs', '250')
    page.fill('#daily_fats', '65')
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')

    print('After valid submit -> URL:', page.url)
    print('Dashboard heading present:',
          'Daily Progress' in page.content() or 'progress' in
          page.content().lower())
    page.screenshot(path='screenshots/after_dashboard_fixed.png',
                    full_page=True)
    print('Saved screenshots/after_dashboard_fixed.png')
    browser.close()
