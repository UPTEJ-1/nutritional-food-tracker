"""
Playwright automation to capture the REAL ZeroDivisionError (BEFORE state).
Logs in, sets daily_calories = 0 (bypassing only the client-side min via
form.submit, proving the server route has no validation), lands on the
dashboard and screenshots the genuine Werkzeug traceback.
"""
import os
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:5000'
USER = 'ncea_tester'
PASSWORD = 'NceaTest123'

os.makedirs('screenshots', exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1280, 'height': 900})

    # Log in
    page.goto(f'{BASE}/login')
    page.fill('#username', USER)
    page.fill('#password', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')

    # Go to goals, set calories to 0, submit past the client-side min guard
    page.goto(f'{BASE}/goals')
    page.fill('#daily_calories', '0')
    page.fill('#daily_protein', '150')
    page.fill('#daily_carbs', '250')
    page.fill('#daily_fats', '65')
    # form.submit() bypasses HTML5 min="1000" so the POST reaches the server
    page.evaluate("document.querySelector('form.goals-form').submit()")
    page.wait_for_load_state('networkidle')

    print('Final URL:', page.url)
    body = page.content()
    print('ZeroDivisionError present in page:',
          'ZeroDivisionError' in body)

    page.screenshot(path='screenshots/before_zerodivision.png', full_page=True)
    print('Saved screenshots/before_zerodivision.png')
    browser.close()
