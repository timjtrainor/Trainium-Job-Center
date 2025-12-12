from playwright.sync_api import Page, expect, sync_playwright
import time

def test_manual_job_ui(page: Page):
    try:
        # 1. Go to the manual add job page (using HashRouter)
        page.goto("http://localhost:5173/#/add-manual-job")
        print(f"Current URL: {page.url}")

        # Wait for hydration
        time.sleep(2)

        # 2. Check for Smart Fill section
        # Trying to find by heading "Smart Fill"
        # It's inside a div, so check for text visibility
        expect(page.get_by_text("Smart Fill")).to_be_visible()

        # 3. Check for textarea
        textarea = page.get_by_placeholder("Paste the raw job posting text here")
        expect(textarea).to_be_visible()

        # 4. Check for button
        button = page.get_by_role("button", name="Auto-Fill Details")
        expect(button).to_be_visible()

        # 5. Take screenshot
        page.screenshot(path="/home/jules/verification/smart_fill_ui.png")
        print("Success!")

    except Exception as e:
        print(f"Failed: {e}")
        page.screenshot(path="/home/jules/verification/error_hash.png")
        raise

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_manual_job_ui(page)
        finally:
            browser.close()
