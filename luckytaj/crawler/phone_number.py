from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
import signal
import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
from selenium.webdriver.support.ui import Select
from datetime import datetime
from collections import defaultdict
from terminal_utils import setup_automation_terminal, cleanup_terminal, print_status

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n[WARNING] Shutdown signal received. Cleaning up...")
    try:
        driver.quit()
        print("[INFO] Browser closed successfully")
    except:
        print("[WARNING] Browser was already closed or unavailable")
    sys.exit(0)

def get_captcha_number(driver, timeout=40):
    wait = WebDriverWait(driver, timeout)
    outer_div = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "div.tracking-normal.space-x-3.text-2xl")
    ))
    digits = outer_div.find_elements(By.TAG_NAME, "span")
    captcha_text = ''.join([d.text for d in digits])
    print(f"[DEBUG] Found {len(digits)} spans, captcha: {captcha_text}")
    return captcha_text

def navigate_to_member_page(driver, config):
    """Navigate to Member > Member Info page after login"""
    wait = WebDriverWait(driver, 40)

    if config.get('has_navigation'):
        # Click "Member" sidebar button
        menu_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='sidebar-item-container']//button[.//div[text()='Member']]")
        ))

        # Wait for ajax loader to finish
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "ajaxLoader"))
        )
        print("[INFO] ajaxLoader complete")
        time.sleep(2)

        menu_link.click()

        # Click "Member Info" submenu
        submenu_item = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[span[@class='bullet-point'] and text()='Member Info']")
        ))
        submenu_item.click()

        # Wait for panel and ajax loader
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, ".box.box-info"))
        )
        print("[INFO] Panel load complete")
        time.sleep(2)

        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "ajaxLoader"))
        )
        print("[INFO] ajaxLoader complete")
        time.sleep(2)

    print(f"[INFO] Navigation complete for {config['name']}")

def set_browser_date(driver, label_text, date_value):
    """Set a date in the browser's calendar picker by label ('Start Date' or 'End Date').
    date_value should be a datetime.date object."""
    month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                   7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
    target_year = str(date_value.year)
    target_month = month_names[date_value.month]
    target_day = str(date_value.day)

    print(f"[INFO] Setting {label_text} to {date_value} ({target_day} {target_month} {target_year})")

    # Click the date picker trigger to open calendar
    trigger = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH,
            f"//div[@class='label' and text()='{label_text}']/following-sibling::div//div[contains(@class,'o-dp-trig')]"
        ))
    )
    trigger.click()
    time.sleep(1)

    # Wait for calendar dropdown to appear
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.o-select-dropdown"))
    )

    # Click the year header button to open year picker
    year_btns = driver.find_elements(By.CSS_SELECTOR, "div.o-select-dropdown button.op-dp-date-btn")
    if len(year_btns) >= 2:
        year_btns[1].click()  # Second button is year
        time.sleep(0.5)

    # Click the target year
    year_cell = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH,
            f"//div[contains(@class,'o-select-dropdown')]//button[contains(@class,'o-dp-year-cell') and text()='{target_year}']"
        ))
    )
    year_cell.click()
    print(f"[INFO] Selected year: {target_year}")
    time.sleep(0.5)

    # Click the target month
    month_cell = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH,
            f"//div[contains(@class,'o-select-dropdown')]//button[contains(@class,'o-dp-month-cell') and text()='{target_month}']"
        ))
    )
    month_cell.click()
    print(f"[INFO] Selected month: {target_month}")
    time.sleep(0.5)

    # Click the target day (not 'light' class - those are next/prev month)
    day_cell = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH,
            f"//div[contains(@class,'o-select-dropdown')]//div[contains(@class,'dpBodyCell') and not(contains(@class,'light')) and text()='{target_day}']"
        ))
    )
    day_cell.click()
    print(f"[INFO] Selected day: {target_day}")
    time.sleep(1)
    print(f"[INFO] {label_text} set to {date_value}")

def click_search_button(driver):
    """Click the Search button after dates are set."""
    search_selectors = [
        (By.XPATH, "//button[contains(text(),'Search')]"),
        (By.XPATH, "//button[.//span[contains(text(),'Search')]]"),
        (By.XPATH, "//*[contains(@class,'btn')][contains(text(),'Search')]"),
        (By.CSS_SELECTOR, "button.search-btn"),
        (By.CSS_SELECTOR, "button[type='submit']"),
    ]
    for by, selector in search_selectors:
        try:
            search_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((by, selector))
            )
            search_button.click()
            print(f"[INFO] Clicked Search button using: {selector}")
            _wait_for_search_animation(driver)
            return
        except Exception:
            continue
    print("[WARNING] Could not find Search button automatically.")
    input("Please click the Search button manually, then press ENTER here to continue...")
    _wait_for_search_animation(driver)


def _wait_for_search_animation(driver):
    """Wait for table refresh to finish after Search is clicked."""
    try:
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "ajaxLoader"))
        )
        print("[INFO] Table refresh complete")
    except Exception:
        print("[DEBUG] ajaxLoader not detected, continuing...")
    time.sleep(1)


def select_per_page(driver, value="50"):
    """Select per-page count from the dropdown (e.g. '50')."""
    try:
        # Click the Per Page dropdown trigger
        per_page_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.row-select-container div.o-dp-trig"))
        )
        per_page_trigger.click()
        time.sleep(1)

        # Click the target option by data-slug
        option = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                f"div.o-select-option span[data-slug='{value}']"
            ))
        )
        driver.execute_script("arguments[0].click();", option)
        print(f"[INFO] Set Per Page to {value}")
        time.sleep(3)
    except Exception as e:
        print(f"[WARNING] Could not set Per Page to {value}: {e}")

# Windows Firefox profile path (comment out if you want a fresh profile)
# profile_path = "C:\\Users\\BDC Computer ll\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\your-profile-name"
# firefox_profile = webdriver.FirefoxProfile(profile_path)

options = Options()
# options.set_preference("profile", profile_path)  # Commented out for fresh profile
# Optional: Use a specific Firefox profile for Windows
# To find your Firefox profiles, navigate to: %APPDATA%\Mozilla\Firefox\Profiles\
# Example Windows profile path:
# options.profile = "C:\\Users\\YourUsername\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\xxxxxxxx.selenium-profile"

# Headless mode if needed
# options.add_argument('--headless')

# ======== Website Configuration ========
website_configs = {
    "1": {
        "name": "luckytaj.com",
        "url": "https://v3-bo.backofficeltaj.com/en-us",
        "merchant_code": "lucky",
        "username": "test_8899",
        "password": "Mcd6033035!",
        "merchant_code_xpath": "//input[@placeholder='Merchant Code']",
        "username_xpath": "//input[@placeholder='Username']",
        "password_xpath": "//input[@placeholder='Password']",
        "has_captcha": True,
        "has_navigation": True,
        "has_status_filter": True,
    },
    "2": {
        "name": "1taj.com",
        "url": "https://admin.1taj.com/#/",
        "username": "tommy8888",
        "password": "tommy6666",
        "username_xpath": "//input[@placeholder='Username']",
        "password_xpath": "//input[@placeholder='Password']",
        "has_captcha": False,
        "has_navigation": False,
        "has_status_filter": False,
    }
}

def select_website():
    """Display menu and get user selection"""
    print("\n" + "="*50)
    print("           SELECT WEBSITE")
    print("="*50)

    for key, config in website_configs.items():
        print(f"{key}. {config['name']}")

    print("="*50)

    while True:
        try:
            choice = input("Enter your choice (1-2): ").strip()
            if choice in website_configs:
                selected_config = website_configs[choice]
                print(f"\n✅ Selected: {selected_config['name']}")
                print(f"🌐 URL: {selected_config['url']}")
                print(f"👤 Username: {selected_config['username']}")
                print("-"*50)
                return selected_config
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
        except KeyboardInterrupt:
            print("\n\n❌ Operation cancelled by user")
            exit(0)

# Setup terminal with custom settings
setup_automation_terminal("Phone Number Crawler")

# Select website configuration BEFORE driver initialization
config = select_website()

# Setup the driver
service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)
driver.maximize_window()

# Login with selected configuration
print(f"\n🚀 Connecting to {config['name']}...")
driver.get(config['url'])
wait = WebDriverWait(driver, 40)

# Merchant code (only for sites that have it)
if 'merchant_code' in config:
    merchant_code_input = wait.until(EC.presence_of_element_located((By.XPATH, config['merchant_code_xpath'])))
    merchant_code_input.send_keys(config['merchant_code'])

# Username + Password
username_input = wait.until(EC.presence_of_element_located((By.XPATH, config['username_xpath'])))
username_input.send_keys(config['username'])
password_input = wait.until(EC.presence_of_element_located((By.XPATH, config['password_xpath'])))
password_input.send_keys(config['password'])

# CAPTCHA handling (luckytaj)
if config.get('has_captcha'):
    captcha_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Captcha Code']")))
    captcha_code = get_captcha_number(driver)
    captcha_input.send_keys(captcha_code)
    print(f"\033[92mExtracted CAPTCHA: {captcha_code}\033[0m")

# Submit (ENTER on last field)
if config.get('has_captcha'):
    captcha_input.send_keys(Keys.ENTER)
else:
    password_input.send_keys(Keys.ENTER)

print(f"✅ Login attempted for {config['name']}")

# ======== Post-Login Navigation ========
navigate_to_member_page(driver, config)

# ======== Date Selection ========
from date_selector import get_date_selection

start_date, end_date = get_date_selection()

if start_date and end_date:
    print(f"\033[1;32m[APPROVED]\033[0m Date range selected: {start_date} to {end_date}")
    print(f"\033[1;33m[INFO]\033[0m Setting dates in browser...")
    set_browser_date(driver, "Register From", start_date)
    set_browser_date(driver, "Register To", end_date)
    click_search_button(driver)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    select_per_page(driver, "50")
    time.sleep(1)
    print(f"\033[1;33m[INFO]\033[0m Using optimized extraction with early stopping")
else:
    print("\033[1;31m[ERROR] No dates selected, exiting...\033[0m")
    driver.quit()
    exit(1)


# ======= Print Logic Here =======

phone_groups = defaultdict(list)


def extract_phone_data(driver, wait_timeout=20):
    """
    Extracts phone data from Member Info table.
    Column mapping: Phone=12, Email=14, Affiliate Code=5.
    Date filtering already handled server-side by Register From/To pickers.
    """

    # Wait until at least one row exists
    WebDriverWait(driver, wait_timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "table tbody tr")) > 0
    )

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"[SUCCESS] Found {len(rows)} rows in Member Information table")

    collected_records = []

    time.sleep(1)  # Stability delay

    for idx in range(len(rows)):
        try:
            # Re-find rows to avoid stale element reference
            current_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            if idx >= len(current_rows):
                print(f"[WARNING] Row {idx + 1} no longer exists. Skipping.")
                continue

            row = current_rows[idx]
            cols = row.find_elements(By.TAG_NAME, 'td')

            if len(cols) < 15:
                continue

            # Filter out summary rows
            first_col_text = cols[0].text.strip()
            if "Page Summary" in first_col_text or "Total Summary" in first_col_text:
                continue

            # Extract data using correct column mapping
            player_id = cols[4].text.strip() if len(cols) > 4 else ""
            phone_number = cols[12].text.strip() if len(cols) > 12 else ""
            email = cols[14].text.strip() if len(cols) > 14 else ""
            affiliate_code = cols[5].text.strip() if len(cols) > 5 else ""

            if phone_number:
                record = {
                    "Player ID": player_id,
                    "Phone Number": phone_number,
                    "Email": email,
                    "Affiliate Code": affiliate_code,
                }
                collected_records.append(record)

        except Exception as e:
            print(f"[ERROR] Failed to process row {idx + 1}: {e}")
            continue

    print(f"[INFO] Collected {len(collected_records)} records from this page")

    return collected_records



def print_grouped_phone_results(grouped_data):
    total_records = sum(len(records) for records in grouped_data.values())
    print(f"\n[INFO] Writing {total_records} total records to file.")

    # Get script directory and build path to result folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels: crawler -> luckytaj -> rocketgo auto
    working_dir = os.path.dirname(os.path.dirname(script_dir))
    result_dir = os.path.join(working_dir, "result")
    os.makedirs(result_dir, exist_ok=True)
    output_file = os.path.join(result_dir, "selenium-phone-number.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        for group, records in grouped_data.items():
            header = f"\n==== {group} ({len(records)} records) ====\n"
            print(f"\033[92m{header}\033[0m")
            f.write(header)

            for i, record in enumerate(records, 1):
                line = (
                    f"#{i} - Phone: {record['Phone Number']}, "
                    f"Player ID: {record['Player ID']}, "
                    f"Email: {record['Email']}, "
                    f"Affiliate: {record.get('Affiliate Code', '')}\n"
                )
                print(line.strip())
                f.write(line)

        footer = f"\n==== TOTAL: {total_records} phone numbers collected ====\n"
        print(f"\033[95m{footer}\033[0m")
        f.write(footer)


def click_next_page(driver, wait_timeout=10):
    try:
        next_button = None

        # Primary: sample_crawler's CSS selector
        try:
            next_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ml-3 button"))
            )
            print("[SUCCESS] Found next button using CSS: div.ml-3 button")
        except Exception:
            pass

        # Fallback: Ant Design selector
        if not next_button:
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.ant-pagination-item-link:has(span[aria-label="right"])'))
                )
                print("[SUCCESS] Found next button using Ant Design selector")
            except Exception:
                pass

        if not next_button:
            print("[WARNING] Could not find Next button with any selector")
            return False

        next_button.click()
        time.sleep(0.5)
        print("[INFO] Clicked on the Next button.")
        return True
    except Exception as e:
        print(f"[WARNING] Could not click Next button: {e}")
        return False


seen_phone_numbers = set()  # Track seen phone numbers to prevent duplicates

def run_optimized_phone_extraction(driver, start_date, end_date):
    """
    Extracts phone data across all pages.
    Date filtering already handled server-side by Register From/To pickers.
    """
    page_counter = 1
    all_collected_records = []
    duplicate_count = 0

    print(f"\033[92m[INFO] Starting phone extraction for date range: {start_date} to {end_date}\033[0m")

    while True:
        print(f"\033[92m[INFO] Scraping page {page_counter}...\033[0m")

        page_records = extract_phone_data(driver)

        # Check for duplicates and add to collection (skip dedup for "-")
        for record in page_records:
            phone_number = record["Phone Number"]
            if phone_number == "-":
                all_collected_records.append(record)
            elif phone_number not in seen_phone_numbers:
                all_collected_records.append(record)
                seen_phone_numbers.add(phone_number)
            else:
                duplicate_count += 1
                print(f"\033[93m[WARNING] Duplicate phone number '{phone_number}' found on page {page_counter}. Skipping.\033[0m")

        print(f"[INFO] Page {page_counter}: Collected {len(page_records)} new records")

        # Try to go to next page
        print(f"[DEBUG] Attempting to navigate to next page...")
        time.sleep(1)
        has_next = click_next_page(driver)
        if not has_next:
            print("[INFO] No more pages found. Finishing extraction.")
            break
        else:
            # Wait for loading animation to appear and disappear
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.anime-shadow"))
                )
                WebDriverWait(driver, 20).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.anime-shadow"))
                )
                print("[INFO] Page loading animation complete")
            except Exception:
                print("[DEBUG] Animation element not detected, continuing...")
            time.sleep(0.5)
            print(f"[SUCCESS] Successfully navigated to page {page_counter + 1}")

        page_counter += 1
        time.sleep(1)

    # Group records for output
    phone_groups = defaultdict(list)
    for record in all_collected_records:
        phone_groups["All"].append(record)

    # Print summary
    total_records = len(all_collected_records)
    print(f"\033[92m[SUMMARY] Extraction completed:\033[0m")
    print(f"  - Pages scraped: {page_counter}")
    print(f"  - Total phone numbers collected: {total_records}")
    print(f"  - Duplicates skipped: {duplicate_count}")

    if total_records > 0:
        print_grouped_phone_results(phone_groups)
    else:
        print("\033[93m[WARNING] No phone numbers found in the specified date range.\033[0m")

def show_post_crawl_menu():
    """Show menu after crawling is complete"""
    import subprocess

    # Get script directory and project root (luckytaj folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Goes up from crawler to luckytaj

    # Define script paths relative to project structure
    scripts = {
        "1": os.path.join(project_root, "add_data", "add-player"),
        "2": os.path.join(script_dir, "transaction.py"),  # In same crawler folder
        "3": os.path.join(project_root, "add_data", "add_deposit"),
    }

    print("\n" + "="*70)
    print("           CRAWLING COMPLETED - SELECT NEXT ACTION")
    print("="*70)
    print("1. Run Add Player Script")
    print("2. Run Deposit Crawler Script")
    print("3. Run Add Deposit Script")
    print("4. Exit")
    print("="*70)

    while True:
        try:
            choice = input("Enter your choice (1-4): ").strip()
            if choice in ["1", "2", "3"]:
                script_path = scripts[choice]
                script_name = os.path.basename(script_path)

                if not os.path.exists(script_path):
                    print(f"❌ Script not found: {script_path}")
                    continue

                print(f"\n🚀 Starting {script_name}...")
                print("="*70)
                subprocess.run(["python", script_path], check=False)
                return
            elif choice == "4":
                print("\n✅ Exiting...")
                return
            else:
                print("❌ Invalid choice. Please enter 1-4.")
        except KeyboardInterrupt:
            print("\n\n❌ Operation cancelled by user")
            return

def main():
    run_optimized_phone_extraction(driver, start_date, end_date)
    time.sleep(5)
    driver.quit()
    cleanup_terminal()

    # Show post-crawl menu
    show_post_crawl_menu()

if __name__ == "__main__":
    # Set up signal handlers for stopping
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Kill command
    print("🚦 Press Ctrl+C to stop the automation at any time")
    print("   (Note: On macOS terminal, use Ctrl+C, not Cmd+C)")
    main()
