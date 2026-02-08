from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
import time
import signal
import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
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

def navigate_to_deposit_page(driver, config):
    """Navigate to the deposit page after login (site-specific)"""
    wait = WebDriverWait(driver, 40)

    if config.get('has_navigation'):
        # Wait for sidebar/main page to load
        menu_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[.//div[text()='Finance Management']]")
        ))

        # Wait for ajax loader to finish
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "ajaxLoader"))
        )
        print("[INFO] ajaxLoader complete")
        time.sleep(2)

        menu_link.click()

        # Click "Deposit" submenu
        submenu_item = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[span[@class='bullet-point'] and text()='Deposit']")
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

    # Status filter (select "Approved")
    if config.get('has_status_filter'):
        status_dropdown = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH,
                "//div[@class='label' and text()='Status']/following-sibling::div//div[contains(@class,'o-input-wrapper')]"
            ))
        )
        status_dropdown.click()
        time.sleep(1)

        approved_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'Approved')]"))
        )
        approved_option.click()
        print("[INFO] Status filter set to 'Approved'")

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
            time.sleep(3)
            return
        except Exception:
            continue
    print("[WARNING] Could not find Search button automatically.")
    input("👉 Please click the Search button manually, then press ENTER here to continue...")
    time.sleep(2)

def select_per_page(driver, value="50"):
    """Select per-page count from the dropdown (e.g. '50')."""
    try:
        # Click the Per Page dropdown trigger
        per_page_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.row-select-container div.o-dp-trig"))
        )
        per_page_trigger.click()
        time.sleep(1)

        # Click the target option
        option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH,
                f"//div[contains(@class,'o-select-dropdown')]//div[contains(@class,'o-select-option') and normalize-space()='{value}'] | "
                f"//div[contains(@class,'o-select-dropdown')]//*[normalize-space()='{value}']"
            ))
        )
        option.click()
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
setup_automation_terminal("Deposit Crawler")

# Select website configuration BEFORE driver initialization
config = select_website()

# Setup the driver with error handling
try:
    print("🔧 Setting up Firefox driver...")
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.maximize_window()
    print("✅ Firefox driver started successfully")
except Exception as e:
    print(f"❌ Firefox driver failed to start: {e}")
    print("\n🔧 Trying alternative Firefox setup...")
    try:
        # Try without GeckoDriverManager
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        service = Service()  # Use system geckodriver
        driver = webdriver.Firefox(service=service, options=options)
        driver.maximize_window()
        print("✅ Firefox driver started with alternative setup")
    except Exception as e2:
        print(f"❌ Alternative Firefox setup also failed: {e2}")
        print("\n🔧 Trying Chrome as fallback...")
        try:
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
            driver.maximize_window()
            print("✅ Chrome driver started successfully as fallback")
        except Exception as e3:
            print(f"❌ Chrome fallback also failed: {e3}")
            print("\n💡 Troubleshooting suggestions:")
            print("1. Make sure Firefox or Chrome is installed and updated")
            print("2. Try restarting your computer")
            print("3. Check if any antivirus is blocking webdrivers")
            print("4. Run as administrator")
            print("5. Try running: pip install --upgrade selenium webdriver-manager")
            sys.exit(1)

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
navigate_to_deposit_page(driver, config)

# ======== Date Selection ========
from date_selector import get_date_selection

start_date, end_date = get_date_selection()

if start_date and end_date:
    print(f"\033[1;32m[APPROVED]\033[0m Date range selected: {start_date} to {end_date}")
    print(f"\033[1;33m[INFO]\033[0m Setting dates in browser...")
    set_browser_date(driver, "Start Date", start_date)
    set_browser_date(driver, "End Date", end_date)
    click_search_button(driver)
    time.sleep(1)
    select_per_page(driver, "50")
    time.sleep(1)
    print(f"\033[1;33m[INFO]\033[0m Using optimized extraction with early stopping")
else:
    print("\033[1;31m[ERROR] No dates selected, exiting...\033[0m")
    driver.quit()
    exit(1)


# ======= Print Logic Here =======

def extract_transaction_data_with_date_filter(driver, start_date, end_date):
    """
    Extracts transaction data using CSS table selectors with early-stopping date filtering.
    Returns (collected_records, should_stop_scraping)
    """
    print(f"[INFO] Filtering for dates: {start_date} to {end_date}")

    # Try different table selectors (from sample_crawler)
    selectors_to_try = [
        "table.tableInfo tbody tr",
        "table.new_data-table tbody tr",
        "table tbody tr",
        ".table tbody tr",
        "tbody tr"
    ]

    rows = []
    working_selector = None

    for selector in selectors_to_try:
        print(f"[DEBUG] Trying selector: {selector}")
        test_rows = driver.find_elements(By.CSS_SELECTOR, selector)
        print(f"[DEBUG] Found {len(test_rows)} rows with selector: {selector}")
        if len(test_rows) > 0:
            rows = test_rows
            working_selector = selector
            print(f"[SUCCESS] Using selector: {selector}")
            break

    if not rows:
        print("[ERROR] No table rows found with any selector!")
        return [], True

    print(f"[INFO] Total rows found: {len(rows)} using selector: {working_selector}")

    collected_records = []
    should_stop_scraping = False

    time.sleep(1)  # Stability delay

    for idx in range(len(rows)):
        try:
            # Re-find rows to avoid stale element reference
            current_rows = driver.find_elements(By.CSS_SELECTOR, working_selector)
            if idx >= len(current_rows):
                print(f"[WARNING] Row {idx + 1} no longer exists. Skipping.")
                continue

            row = current_rows[idx]
            cols = row.find_elements(By.TAG_NAME, 'td')

            if len(cols) < 10:
                print(f"[WARNING] Row {idx + 1} has only {len(cols)} columns. Skipping.")
                continue

            # Skip summary rows
            first_col_text = cols[0].text.strip()
            if "Page Summary" in first_col_text or "Total Summary" in first_col_text:
                print(f"[INFO] Skipping summary row: '{first_col_text}'")
                continue

            # Extract time from column 20 (format: 'YYYY-MM-DD HH:MM:SS')
            full_date_str = cols[20].text.strip() if len(cols) > 20 else ""
            if not full_date_str:
                print(f"[WARNING] No date in row {idx + 1}, skipping")
                continue

            try:
                date_str = full_date_str.split(" ")[0]
                row_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                # Date filtering logic with early stopping
                if row_date > end_date:
                    print(f"[DEBUG] Row {idx + 1} too new ({row_date}), skipping")
                    continue

                if row_date < start_date:
                    print(f"[INFO] Row {idx + 1} too old ({row_date}), stopping scraping")
                    should_stop_scraping = True
                    break

                # Parse amount from column 9 (strip "Rs" and commas)
                amount_text = cols[9].text.strip().replace("Rs", "").replace(",", "").strip()
                try:
                    amount = float(amount_text) if amount_text else 0.0
                except ValueError:
                    print(f"[WARNING] Invalid amount '{amount_text}' in row {idx + 1}, setting to 0.0")
                    amount = 0.0

                # Parse tax fee from column 12
                tax_text = cols[12].text.strip().replace(",", "")
                try:
                    tax_fee = float(tax_text) if tax_text else 0.0
                except ValueError:
                    print(f"[WARNING] Invalid tax fee '{tax_text}' in row {idx + 1}, setting to 0.0")
                    tax_fee = 0.0

                # Create record using sample_crawler column mapping
                record = {
                    "Order ID": cols[0].text.strip(),
                    "Phone Number": cols[5].text.strip(),
                    "Amount": amount,
                    "Tax Fee": tax_fee,
                    "Time": full_date_str,
                    "Gateway": cols[21].text.strip() if len(cols) > 21 else "Unknown",
                    "Date": row_date
                }
                collected_records.append(record)

            except ValueError as e:
                print(f"[WARNING] Invalid date format '{full_date_str}' in row {idx + 1}: {e}")
                continue

        except Exception as e:
            print(f"[ERROR] Failed to process row {idx + 1}: {e}")
            continue

    print(f"[INFO] Collected {len(collected_records)} records from this page")
    print(f"[INFO] Should stop scraping: {should_stop_scraping}")

    return collected_records, should_stop_scraping



def print_grouped_results(gateway_groups):
    print(f"[DEBUG] print_grouped_results called with {len(gateway_groups)} gateway groups")
    for gateway, records in gateway_groups.items():
        print(f"[DEBUG] Gateway '{gateway}' has {len(records)} records")

    grand_total = 0
    grand_tax_total = 0

    # Get script directory and build path to result folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels: crawler -> luckytaj -> rocketgo auto
    working_dir = os.path.dirname(os.path.dirname(script_dir))
    result_dir = os.path.join(working_dir, "result")
    os.makedirs(result_dir, exist_ok=True)
    output_file = os.path.join(result_dir, "selenium-transaction_history.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write("                              DEPOSITS\n")
        f.write("="*80 + "\n")
        print(f"\033[92m{'='*80}\033[0m")
        print(f"\033[92m                              DEPOSITS\033[0m")
        print(f"\033[92m{'='*80}\033[0m")

        for gateway, records in gateway_groups.items():
            total_amount = sum(record["Amount"] if isinstance(record["Amount"], (int, float)) else float(record["Amount"].replace(",", "")) for record in records)
            grand_total += total_amount

            total_tax_amount = sum(float(record.get("Tax Fee", 0)) for record in records)
            grand_tax_total += total_tax_amount

            header = f"\n==== {gateway} ({len(records)} record{'s' if len(records) != 1 else ''}) | Total Amount: Rs {total_amount:,.2f} | Total Fee: Rs {total_tax_amount:.2f} ====\n"
            print(f"\033[92m{header}\033[0m")
            f.write(header)

            # Sort records by time (latest first) with error handling
            def safe_parse_time(record):
                try:
                    if record["Time"] and record["Time"].strip():
                        return datetime.strptime(record["Time"], "%Y-%m-%d %H:%M:%S")
                    else:
                        return datetime.min
                except ValueError:
                    print(f"[WARNING] Invalid time format: '{record['Time']}'")
                    return datetime.min

            sorted_records = sorted(records, key=safe_parse_time, reverse=True)

            for i, record in enumerate(sorted_records, 1):
                entry = (
                    f"\nRecord #{i}\n"
                    f"Order ID: {record['Order ID']}\n"
                    f"Phone Number: {record['Phone Number']}\n"
                    f"Amount: {record['Amount']:,.2f}\n"
                    f"Tax Fee: {record.get('Tax Fee', 0)}\n"
                    f"Time: {record['Time']}\n"
                )
                print(f"\033[94m{entry}\033[0m")
                f.write(entry)

            footer = f"\n>> Total Amount for {gateway}: Rs {total_amount:,.2f}\n"
            print(f"\033[93m{footer}\033[0m")
            f.write(footer)

        total_records = sum(len(records) for records in gateway_groups.values())

        # Grand total summary
        f.write("\n")
        grand_total_header = f"=========================== GRAND TOTAL for All Gateways ===========================\n\n"
        print(f"\033[92m{grand_total_header}\033[0m", end="")
        f.write(grand_total_header)

        print(f"\033[95m  DEPOSITS Records: \033[92m{total_records}\033[95m\n\n\033[0m", end="")
        f.write(f"  DEPOSITS Records: {total_records}\n\n")

        # Per-gateway summary
        for gateway, records in gateway_groups.items():
            gateway_amount = sum(r["Amount"] for r in records)
            total_tax_amount = round(sum(float(r.get("Tax Fee", 0)) for r in records), 2)

            # Extract date from the first record's time
            try:
                if records[0]["Time"] and records[0]["Time"].strip():
                    transaction_date = datetime.strptime(records[0]["Time"], "%Y-%m-%d %H:%M:%S").strftime("%m/%d/%Y")
                else:
                    transaction_date = "Unknown"
            except (ValueError, IndexError):
                transaction_date = "Unknown"

            gateway_header = f"==== pg {gateway}_{transaction_date} ====\n\n"
            print(f"\033[92m{gateway_header}\033[0m", end="")
            f.write(gateway_header)

            print(f"\033[95m  DEPOSITS Records: \033[92m{len(records)}\033[95m\n\033[0m", end="")
            print(f"\033[95m  DEPOSITS Amount: \033[92m{gateway_amount:,.2f}\033[95m\n\n\033[0m", end="")
            f.write(f"  DEPOSITS Records: {len(records)}\n")
            f.write(f"  DEPOSITS Amount: {gateway_amount:,.2f}\n\n")

            gateway_tax_line = f"(depo) pg {gateway} {transaction_date} | Total Fee: Rs {total_tax_amount:.2f}\n"
            print(f"\033[95m{gateway_tax_line}\033[0m")
            f.write(gateway_tax_line)



def click_next_page(driver, wait_timeout=10):
    try:
        # Try sample_crawler's selector first, then Ant Design fallbacks
        css_selectors = [
            ("div.ml-3 button", "CSS_SELECTOR"),
        ]
        xpath_selectors = [
            "//li[@title='Next Page' and @aria-disabled='false']//button[@class='ant-pagination-item-link']",
            "//button[@class='ant-pagination-item-link']",
        ]

        next_button = None
        print("[DEBUG] Searching for Next button...")

        # Try CSS selectors first
        for selector, _ in css_selectors:
            try:
                print(f"[DEBUG] Trying CSS: {selector}")
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"[SUCCESS] Found next button using CSS: {selector}")
                break
            except Exception as e:
                print(f"[DEBUG] Failed: {e}")
                continue

        # Try XPath selectors as fallback
        if not next_button:
            for selector in xpath_selectors:
                try:
                    print(f"[DEBUG] Trying XPath: {selector}")
                    next_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"[SUCCESS] Found next button using XPath: {selector}")
                    break
                except Exception as e:
                    print(f"[DEBUG] Failed: {e}")
                    continue

        if not next_button:
            print("[ERROR] Could not find Next button with any selector")
            return False

        # Try multiple click strategies
        # Strategy 1: Regular click
        try:
            next_button.click()
            time.sleep(.5)
            print("[INFO] Successfully clicked Next button with regular click")
            return True
        except Exception as e:
            print(f"[DEBUG] Regular click failed: {e}")

        # Strategy 2: JavaScript click
        try:
            print("[DEBUG] Trying JavaScript click...")
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
            print("[INFO] Successfully clicked Next button with JavaScript")
            return True
        except Exception as e:
            print(f"[DEBUG] JavaScript click failed: {e}")

        # Strategy 3: Action chains click
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            print("[DEBUG] Trying ActionChains click...")
            ActionChains(driver).move_to_element(next_button).click().perform()
            time.sleep(2)
            print("[INFO] Successfully clicked Next button with ActionChains")
            return True
        except Exception as e:
            print(f"[DEBUG] ActionChains click failed: {e}")

        # Strategy 4: Scroll into view then click
        try:
            print("[DEBUG] Trying scroll into view then click...")
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)
            next_button.click()
            time.sleep(2)
            print("[INFO] Successfully clicked Next button after scrolling into view")
            return True
        except Exception as e:
            print(f"[DEBUG] Scroll + click failed: {e}")

        print("[ERROR] All click strategies failed")
        return False

    except Exception as e:
        print(f"[WARNING] Could not click Next button: {e}")
        return False




gateway_groups = defaultdict(list)  # Global collector
seen_order_ids = set()  # Track seen Order IDs to prevent duplicates


def run_optimized_transaction_extraction(driver, start_date, end_date):
    """
    Optimized extraction with early stopping based on date range.
    Stops scraping when encountering dates older than start_date.
    """
    page_counter = 1
    all_collected_records = []
    duplicate_count = 0
    stop_scraping = False
    
    print(f"\033[92m[INFO] Starting optimized extraction for date range: {start_date} to {end_date}\033[0m")
    
    while not stop_scraping:
        print(f"\033[92m[INFO] Scraping page {page_counter}...\033[0m")
        
        # Extract data from current page with date filtering
        page_records, should_stop = extract_transaction_data_with_date_filter(
            driver, start_date, end_date
        )
        
        # Check for duplicates and add to collection
        for record in page_records:
            order_id = record["Order ID"]
            if order_id not in seen_order_ids:
                all_collected_records.append(record)
                seen_order_ids.add(order_id)
            else:
                duplicate_count += 1
                print(f"\033[93m[WARNING] Duplicate Order ID '{order_id}' found on page {page_counter}. Skipping.\033[0m")
        
        print(f"[INFO] Page {page_counter}: Collected {len(page_records)} new records")
        
        # Check if we should stop scraping
        if should_stop:
            print(f"\033[93m[INFO] Reached date boundary. Stopping extraction at page {page_counter}.\033[0m")
            stop_scraping = True
            break
        
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
    
    # Group records by gateway for output
    gateway_groups = defaultdict(list)
    for record in all_collected_records:
        gateway_groups[record["Gateway"]].append(record)
    
    # Print summary
    total_records = len(all_collected_records)
    print(f"\033[92m[SUMMARY] Extraction completed:\033[0m")
    print(f"  - Pages scraped: {page_counter}")
    print(f"  - Total records collected: {total_records}")
    print(f"  - Unique gateways: {len(gateway_groups)}")
    print(f"  - Duplicates skipped: {duplicate_count}")
    
    if total_records > 0:
        print_grouped_results(gateway_groups)
    else:
        print("\033[93m[WARNING] No records found in the specified date range.\033[0m")
    
def show_post_crawl_menu():
    """Show menu after crawling is complete"""
    import subprocess

    # Get script directory and project root (luckytaj folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Goes up from crawler to luckytaj

    # Define script paths relative to project structure
    scripts = {
        "1": os.path.join(script_dir, "phone_number.py"),  # In same crawler folder
        "2": os.path.join(project_root, "add_data", "add_deposit"),
        "3": os.path.join(project_root, "add_data", "add-player"),
    }

    print("\n" + "="*70)
    print("           CRAWLING COMPLETED - SELECT NEXT ACTION")
    print("="*70)
    print("1. Run Phone Number Crawler Script")
    print("2. Run Add Deposit Script (with start Order ID configuration)")
    print("3. Run Add Player Script")
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
    run_optimized_transaction_extraction(driver, start_date, end_date)
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