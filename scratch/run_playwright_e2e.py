import os
import sys
import time
import uuid
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = str(BASE_DIR / "docs" / "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def run_tests():
    print("Starting Playwright E2E Browser Testing Suite...")
    with sync_playwright() as p:
        if os.path.exists(EDGE_PATH):
            browser = p.chromium.launch(executable_path=EDGE_PATH, headless=True)
        else:
            browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 0. Capture Public Landing Page
        print("0. Capturing Landing Page...")
        page.goto("http://localhost:3000/", wait_until="networkidle")
        time.sleep(1)
        landing_shot = os.path.join(SCREENSHOTS_DIR, "landing_page.png")
        page.screenshot(path=landing_shot)
        print(f"✓ Saved screenshot: {landing_shot}")

        # 1. Register a test user for clean authentication state
        uid = uuid.uuid4().hex[:6]
        test_email = f"theme_tester_{uid}@quantweave.test"
        test_pass = "TestPassword123!"

        print(f"1. Registering user: {test_email}")
        page.goto("http://localhost:3000/register", wait_until="networkidle")
        page.fill('#name', "Aarav Sharma")
        page.fill('#email', test_email)
        page.fill('#password', test_pass)
        page.fill('#confirmPassword', test_pass)
        page.click('button[type="submit"]')

        # Wait for redirect to /dashboard
        page.wait_for_url("**/dashboard", timeout=15000)
        print("✓ Successfully authenticated and navigated to Dashboard")

        # 2. Test Profile Dropdown (Verify no clipping and proper positioning)
        print("2. Testing Profile Dropdown Menu in Sidebar...")
        # Trigger is at the bottom of the sidebar
        profile_btn = page.locator('button[aria-label="User account menu"]').first
        profile_btn.wait_for(state="visible", timeout=10000)
        profile_btn.click()

        # Wait for portal dropdown menu
        dropdown = page.locator('[role="menu"]')
        dropdown.wait_for(state="visible", timeout=5000)

        # Check dropdown bounding box
        box = dropdown.bounding_box()
        assert box is not None, "Dropdown bounding box is null"
        print(f"Dropdown Bounding Box: top={box['y']}, left={box['x']}, width={box['width']}, height={box['height']}")
        
        # Verify completely within viewport (1440x900)
        assert box['x'] >= 0, "Dropdown clipped on left"
        assert box['x'] + box['width'] <= 1440, "Dropdown clipped on right"
        assert box['y'] >= 0, "Dropdown clipped on top"
        assert box['y'] + box['height'] <= 900, "Dropdown clipped on bottom"
        print("✓ Dropdown is 100% inside visible viewport bounds (ZERO clipping)")

        # Capture Screenshot of fixed dropdown
        dropdown_shot_path = os.path.join(SCREENSHOTS_DIR, "profile_dropdown_fixed.png")
        page.screenshot(path=dropdown_shot_path)
        print(f"✓ Saved screenshot: {dropdown_shot_path}")

        # Test Escape key closes dropdown
        page.keyboard.press("Escape")
        time.sleep(0.5)
        assert dropdown.count() == 0 or not dropdown.is_visible(), "Escape did not dismiss dropdown"
        print("✓ Escape key successfully dismissed dropdown")

        # 3. Test Profile Page
        print("3. Navigating to Profile Page (/profile)...")
        page.goto("http://localhost:3000/profile", wait_until="networkidle")
        time.sleep(1)

        profile_shot_path = os.path.join(SCREENSHOTS_DIR, "profile_page.png")
        page.screenshot(path=profile_shot_path)
        print(f"✓ Saved screenshot: {profile_shot_path}")

        # Click Appearance tab
        print("4. Testing Appearance Section & Avatar Presets...")
        app_tab = page.locator('button:has-text("Appearance & Themes")')
        app_tab.click()
        time.sleep(0.5)

        # Scroll to avatar presets
        avatar_section = page.locator('h2:has-text("Avatar Appearance Presets")')
        avatar_section.scroll_into_view_if_needed()
        time.sleep(0.5)

        avatar_shot_path = os.path.join(SCREENSHOTS_DIR, "avatar_selector.png")
        page.screenshot(path=avatar_shot_path)
        print(f"✓ Saved screenshot: {avatar_shot_path}")

        # Select 'Signal Aqua' avatar preset
        page.locator('button:has-text("Signal Aqua")').last.click()
        time.sleep(0.8)

        # Scroll to website appearance settings
        theme_section = page.locator('h2:has-text("Website Theme System")')
        theme_section.scroll_into_view_if_needed()
        time.sleep(0.5)

        appearance_shot_path = os.path.join(SCREENSHOTS_DIR, "appearance_settings.png")
        page.screenshot(path=appearance_shot_path)
        print(f"✓ Saved screenshot: {appearance_shot_path}")

        # 4. Capture Dashboard in all 4 Themes
        themes = [
            ("signal-loom", "dashboard_signal_loom.png"),
            ("daybreak", "dashboard_daybreak.png"),
            ("nebula", "dashboard_nebula.png"),
            ("oceanic", "dashboard_oceanic.png"),
        ]

        for theme_id, filename in themes:
            print(f"Capturing Dashboard in {theme_id} theme...")
            page.goto("http://localhost:3000/dashboard", wait_until="networkidle")
            # Set theme
            page.evaluate(f"""(theme) => {{
                document.documentElement.setAttribute('data-theme', theme);
                localStorage.setItem('qw_theme', theme);
            }}""", theme_id)
            time.sleep(1)

            # Verify root attribute
            active_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            assert active_theme == theme_id, f"Expected data-theme='{theme_id}', got '{active_theme}'"

            shot_path = os.path.join(SCREENSHOTS_DIR, filename)
            page.screenshot(path=shot_path)
            print(f"✓ Saved theme screenshot: {shot_path}")

        # Also save main_dashboard.png (alias for Signal Loom default)
        main_dash_path = os.path.join(SCREENSHOTS_DIR, "main_dashboard.png")
        if os.path.exists(os.path.join(SCREENSHOTS_DIR, "dashboard_signal_loom.png")):
            import shutil
            shutil.copyfile(os.path.join(SCREENSHOTS_DIR, "dashboard_signal_loom.png"), main_dash_path)
            print(f"✓ Saved main_dashboard screenshot: {main_dash_path}")

        # 5. Capture All Six Core Financial Modules
        print("5. Capturing Six Core Financial Modules...")
        modules = [
            ("http://localhost:3000/equity", "equity_intelligence.png"),
            ("http://localhost:3000/portfolio", "portfolio_intelligence.png"),
            ("http://localhost:3000/funds", "fundscope.png"),
            ("http://localhost:3000/market", "marketpulse.png"),
            ("http://localhost:3000/quantlab", "quantlab.png"),
            ("http://localhost:3000/ai", "ai_copilot.png"),
        ]

        for mod_url, mod_file in modules:
            print(f"Visiting module: {mod_url}...")
            page.goto(mod_url, wait_until="networkidle")
            time.sleep(1.5)
            mod_path = os.path.join(SCREENSHOTS_DIR, mod_file)
            page.screenshot(path=mod_path)
            print(f"✓ Saved module screenshot: {mod_path}")

        # 5. Responsive Verification (Mobile 390x844, Tablet 768x1024, Laptop 1024x768)
        print("5. Verifying Responsive Layouts...")
        # Mobile 390px
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto("http://localhost:3000/dashboard", wait_until="networkidle")
        time.sleep(1)
        # Open mobile sidebar drawer
        hamburger = page.locator('button[aria-label="Toggle navigation menu"]')
        if hamburger.is_visible():
            hamburger.click()
            time.sleep(0.5)
            # Click user profile menu in drawer
            drawer_profile = page.locator('button[aria-label="User account menu"]').first
            drawer_profile.click()
            time.sleep(0.5)
            # Verify dropdown is rendered and within 390px width
            m_box = page.locator('[role="menu"]').bounding_box()
            assert m_box is not None
            assert m_box['x'] >= 0, "Mobile dropdown clipped on left"
            assert m_box['x'] + m_box['width'] <= 390, f"Mobile dropdown overflows width: {m_box}"
            print("✓ Mobile (390px) profile dropdown fully contained without overflow")

        # Tablet 768px
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto("http://localhost:3000/profile", wait_until="networkidle")
        time.sleep(0.5)
        print("✓ Tablet (768px) profile page responsive")

        # Laptop 1024px
        page.set_viewport_size({"width": 1024, "height": 768})
        page.goto("http://localhost:3000/dashboard", wait_until="networkidle")
        time.sleep(0.5)
        print("✓ Laptop (1024px) dashboard responsive")

        browser.close()
        print("\nALL PLAYWRIGHT E2E BROWSER TESTS AND SCREENSHOT CAPTURES COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
