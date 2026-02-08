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
        print("⚠️ Browser was already closed or unavailable")
    sys.exit(0)




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
        "name": "NepalWin",
        "url": "https://bo.nepalwin.com/user/login",
        "username": "kewlim888",
        "password": "aaaa1111",
        "username_xpath": "//input[@placeholder='Username:']",
        "password_xpath": "//input[@placeholder='Password:']"
    },
    "2": {
        "name": "95np",
        "url": "https://bo.95np.com/user/login/",
        "username": "tommy8888",
        "password": "tommy6666",
        "username_xpath": "//input[@placeholder='Username:']",
        "password_xpath": "//input[@placeholder='Password:']"
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
username_input = wait.until(EC.presence_of_element_located((By.XPATH, config['username_xpath'])))
username_input.send_keys(config['username'])

wait = WebDriverWait(driver, 40)
password_input = wait.until(EC.presence_of_element_located((By.XPATH, config['password_xpath'])))
password_input.send_keys(config['password'])
password_input.send_keys(Keys.ENTER)

print(f"✅ Login attempted for {config['name']}")

time.sleep(2)

# ======== Entered Main Page ========

# Wait until the Transaction header is present and visible
transaction_header = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, "//span[@class='ant-page-header-heading-title' and text()='Transaction']"))
)

print("✅ 'Transaction' header found, proceeding...")

# Wait until the 'Report' menu item is visible and clickable
report_item = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//span[text()='Report']"))
)

# Click it
report_item.click()
time.sleep(2)


# ======== Entered Player Page ========

# Wait until the link is visible and clickable

# Wait for and click the Bank menu item
selectors_to_try = [
    # Primary selector for the exact Bank menu item you showed
    "//span[@class='ant-pro-menu-item' and @title='Bank']",
    # Alternative selectors
    "//span[contains(@class,'ant-pro-menu-item') and @title='Bank']",
    "//span[@title='Bank']//span[@class='ant-pro-menu-item-title' and text()='Bank']/..",
    "//span[contains(@class,'ant-pro-menu-item-title') and text()='Bank']/.."
]

bank_item = None
for selector in selectors_to_try:
    try:
        print(f"[DEBUG] Trying Bank selector: {selector}")
        bank_item = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, selector))
        )
        print(f"[SUCCESS] Found Bank menu item using: {selector}")
        break
    except Exception as e:
        print(f"[DEBUG] Bank selector failed: {e}")
        continue

if bank_item:
    bank_item.click()
    print("✅ Clicked 'Bank' successfully.")
else:
    print("❌ Could not find Bank menu item")
    driver.quit()
    exit(1)

time.sleep(.5)

link = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "Bank Report"))
)

# Click the link
link.click()
print("Clicked 'Bank Report' successfully.")


# Select date section
from date_selector import get_date_selection, DateSelector

# Use date selection modal
start_date, end_date = get_date_selection()

if start_date and end_date:
    print(f"\033[1;32m[APPROVED]\033[0m Date range selected: {start_date} to {end_date}")
    print(f"\033[1;33m[INFO]\033[0m Using optimized extraction with early stopping")
else:
    print("\033[1;31m[ERROR] No dates selected, exiting...\033[0m")
    driver.quit()
    exit(1)

# ======== Entered Main Page ========

# Wait for sidebar to appear





# ======== Entered "Bank Report" =======


# Wait for panel loading
WebDriverWait(driver, 20).until(
    EC.invisibility_of_element_located((By.CSS_SELECTOR, ".box.box-info"))
)
print("[INFO] Panel load complete")


time.sleep(2)

# Wait for ajax loader loading
WebDriverWait(driver, 20).until(
    EC.invisibility_of_element_located((By.CLASS_NAME, "ajaxLoader"))
)
print("\033[94m[INFO] ajaxLoader complete\033[0m")

time.sleep(2)






# ======= Print Logic Here =======

phone_groups = defaultdict(list)


def extract_phone_data_with_date_filter(driver, start_date, end_date, wait_timeout=20):
    """
    Extracts phone data with early-stopping date filtering.
    Returns (collected_records, should_stop_scraping)
    """
    print(f"[INFO] Filtering for dates: {start_date} to {end_date}")
    
    # Wait until at least one row exists
    WebDriverWait(driver, wait_timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "table tbody tr")) > 0
    )

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    print(f"[SUCCESS] Found {len(rows)} rows in Member Information table")

    collected_records = []
    should_stop_scraping = False
    
    print(f"[INFO] Processing {len(rows)} rows with date filtering...")
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
            
            if len(cols) < 5:  # Reduce minimum column requirement
                print(f"[WARNING] Row {idx + 1} has only {len(cols)} columns. Skipping.")
                continue
            
            # Filter out summary rows
            first_col_text = cols[0].text.strip() if len(cols) > 0 else ""
            if "Page Summary" in first_col_text or "Total Summary" in first_col_text:
                print(f"[INFO] Skipping summary row: '{first_col_text}'")
                continue

            # DEBUG: Print all column data to identify the date column
            print(f"\n[DEBUG] Row {idx + 1} - Total columns: {len(cols)}")
            for col_idx, col in enumerate(cols):
                col_text = col.text.strip()
                print(f"[DEBUG] Column {col_idx}: '{col_text}'")
                
            # Extract date from appropriate column (you need to identify which column has dates)
            registration_date_str = cols[0].text.strip() if len(cols) > 0 else ""
            print(f"[DEBUG] Trying to parse date from column 0: '{registration_date_str}'")
            
            if not registration_date_str:
                print(f"[WARNING] No registration date in row {idx + 1}, skipping")
                continue
            
            try:
                # Parse registration date - support multiple formats for Windows compatibility
                date_formats = [
                    "%Y-%m-%d",          # 2025-08-27
                    "%m/%d/%Y",          # 08/27/2025 (US format)
                    "%d/%m/%Y",          # 27/08/2025 (European format)
                    "%Y/%m/%d",          # 2025/08/27
                    "%d-%m-%Y",          # 27-08-2025
                    "%m-%d-%Y",          # 08-27-2025
                    "%d.%m.%Y",          # 27.08.2025 (German format)
                    "%Y%m%d"             # 20250827 (compact format)
                ]
                
                # Extract date part if datetime string
                if ' ' in registration_date_str:
                    date_str = registration_date_str.split(" ")[0]  # Extract date part
                else:
                    date_str = registration_date_str
                
                row_date = None
                for date_format in date_formats:
                    try:
                        row_date = datetime.strptime(date_str, date_format).date()
                        print(f"[DEBUG] Successfully parsed '{date_str}' using format '{date_format}'")
                        break
                    except ValueError:
                        continue
                
                if row_date is None:
                    raise ValueError(f"Unable to parse date '{date_str}' with any known format")
                
                print(f"[DEBUG] Row {idx + 1}: Date {row_date}, Range {start_date} to {end_date}")
                
                # Date filtering logic
                if row_date > end_date:
                    print(f"[DEBUG] Row {idx + 1} too new ({row_date}), skipping")
                    continue
                
                if row_date < start_date:
                    print(f"[INFO] Row {idx + 1} too old ({row_date}), stopping scraping")
                    should_stop_scraping = True
                    break

                # Row is within date range (start_date <= row_date <= end_date)
                # Filter transaction type {"CASH_IN", "CASH_OUT"} first
                txn_type = cols[2].text.strip() if len(cols) > 2 else ""
                print(f"[DEBUG] Row {idx + 1}: Found transaction type '{txn_type}'")

                if txn_type.upper() not in ("CASH_IN", "CASH_OUT"):
                    print(f"[DEBUG] Row {idx + 1}: Skipping '{txn_type}' - not in allowed list")
                    continue

                print(f"[INFO] Row {idx + 1}: Collecting '{txn_type}' transaction")
                amount_text = cols[3].text.strip().replace("Rs", "").replace(",", "").strip()
                try:
                    amount = float(amount_text) if amount_text else 0.0
                except ValueError:
                    print(f"[WARNING] Invalid amount '{amount_text}' in row {idx + 1}, setting to 0.0")
                    amount = 0.0

                
                # Row is within date range (start_date <= row_date <= end_date)
                print(f"[INFO] Row {idx + 1} within range ({row_date}), collecting")
                
                phone_number = cols[3].text.strip() if len(cols) > 3 else ""
                remark_raw = cols[5].text.strip() if len(cols) > 5 else ""
                
                # Convert remark to descriptive text
                if remark_raw == "0" or remark_raw == "" or not remark_raw:
                    remark = "No additional details"
                elif remark_raw.replace(".", "").isdigit():
                    # If it's a number, add context
                    if txn_type.upper() == "CASH_IN":
                        remark = f"Deposit reference: {remark_raw}"
                    elif txn_type.upper() == "CASH_OUT":
                        remark = f"Withdrawal reference: {remark_raw}"
                    else:
                        remark = f"Transaction reference: {remark_raw}"
                else:
                    remark = remark_raw

                # Create the record
                record = {
                    "Transaction Type": txn_type,
                    "Amount": amount,  
                    "Remark": remark,
                    "Phone Number": phone_number,  # Add phone number field
                    "Date": row_date,  # Add parsed date for easier processing
                    "Time": registration_date_str  # Add full timestamp
                }
                collected_records.append(record)

            except ValueError as e:
                print(f"[WARNING] Invalid date format '{registration_date_str}' in row {idx + 1}: {e}")
                continue
                
        except Exception as e:
            print(f"[ERROR] Failed to process row {idx + 1}: {e}")
            continue

    print(f"[INFO] Collected {len(collected_records)} records from this page")
    print(f"[INFO] Should stop scraping: {should_stop_scraping}")
    
    return collected_records, should_stop_scraping



def print_grouped_phone_results(grouped_data):
    total_records = sum(len(records) for records in grouped_data.values())
    print(f"\n[INFO] Writing {total_records} total records to calculated_result.txt file.")

    # Keywords to track (case insensitive)
    keywords = ["Hima8", "Jeeraj", "95np", "NepalWin", "Np321", "Money Changer", "RajaNepal", "royalnepa"]
    keyword_totals = {keyword.lower(): {"CASH_IN": 0.0, "CASH_OUT": 0.0} for keyword in keywords}
    money_changer_times = []  # Special tracking for Money Changer times
    
    # Collect all records from all groups
    all_records = []
    record_counter = 1
    
    for records in grouped_data.values():
        for record in records:
            transaction_type = record.get("Transaction Type", "Unknown")
            amount = float(record.get('Amount', 0))
            remark = record.get("Remark", "-")
            
            # Find the first keyword that appears in the remark (case insensitive)
            detected_keyword = None
            remark_lower = remark.lower()
            
            # Special exception: if remark contains specific Hima8 phrases, assume NepalWin
            if ("use hima8 muktinath bank approve" in remark_lower or 
                "use hima8 muktinath bank withdraw" in remark_lower):
                detected_keyword = "nepalwin"
            else:
                # Normal keyword detection - find first appearing keyword
                earliest_position = len(remark)
                
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    position = remark_lower.find(keyword_lower)
                    if position != -1 and position < earliest_position:
                        earliest_position = position
                        detected_keyword = keyword_lower
            
            # Track totals for detected keyword
            if detected_keyword:
                if transaction_type == "CASH_IN":
                    keyword_totals[detected_keyword]["CASH_IN"] += amount
                elif transaction_type == "CASH_OUT":
                    keyword_totals[detected_keyword]["CASH_OUT"] += amount
                
                # Special tracking for Money Changer times and remarks
                if detected_keyword == "money changer":
                    time_value = record.get("Time", record.get("Date", "Unknown"))
                    remark_value = remark
                    money_changer_times.append({"time": time_value, "remark": remark_value})
            
            all_records.append({
                "number": record_counter,
                "transaction_type": transaction_type,
                "amount": f"{amount:.2f}",
                "remark": remark,
                "time": record.get("Time", record.get("Date", "Unknown")),
                "keyword": detected_keyword
            })
            record_counter += 1
    
    # Write to calculated_result.txt file
    with open("selenium_project/calculated_result.txt", "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("           CALCULATION RESULTS\n")
        f.write("=" * 60 + "\n\n")
        
        for record in all_records:
            f.write(f"Record #{record['number']}\n")
            f.write(f"Transaction Type: {record['transaction_type']}\n")
            f.write(f"Amount: {record['amount']}\n")
            f.write(f"Remark: {record['remark']}\n")
            f.write(f"Time: {record['time']}\n")
            if record['keyword']:
                f.write(f"Keyword: {record['keyword'].title()}\n")
            f.write("-" * 30 + "\n")
        
        f.write(f"\nTotal Records: {total_records}\n")
        f.write("=" * 60 + "\n")
        f.write("           KEYWORD TOTALS\n")
        f.write("=" * 60 + "\n")
        
        # Write keyword totals
        for keyword in keywords:
            cash_in_total = keyword_totals[keyword.lower()]["CASH_IN"]
            cash_out_total = keyword_totals[keyword.lower()]["CASH_OUT"]
            f.write(f"{keyword}\n")
            f.write(f"CASH_IN: {cash_in_total:.2f}\n")
            f.write(f"CASH_OUT: {cash_out_total:.2f}\n")
            
            # Special handling for Money Changer - show all times and remarks
            if keyword.lower() == "money changer" and money_changer_times:
                for entry in money_changer_times:
                    f.write(f"Time: {entry['time']}, Remark: {entry['remark']}\n")
            
            f.write("-" * 30 + "\n")
        
        f.write("=" * 60 + "\n")
    
    # Also print to console in the same format
    print(f"\033[92m{'='*50}\033[0m")
    print(f"\033[92m           CALCULATION RESULTS\033[0m")
    print(f"\033[92m{'='*50}\033[0m")
    
    for record in all_records:
        print(f"\033[95mRecord #{record['number']}\033[0m")
        print(f"Transaction Type: {record['transaction_type']}")
        print(f"Amount: {record['amount']}")
        print(f"Remark: {record['remark']}")
        print(f"Time: {record['time']}")
        if record['keyword']:
            print(f"Keyword: \033[93m{record['keyword'].title()}\033[0m")
        print("-" * 30)
    
    print(f"\033[92mTotal Records: {total_records}\033[0m")
    print(f"\033[92m{'='*50}\033[0m")
    print(f"\033[92m           KEYWORD TOTALS\033[0m")
    print(f"\033[92m{'='*50}\033[0m")
    
    # Print keyword totals
    for keyword in keywords:
        cash_in_total = keyword_totals[keyword.lower()]["CASH_IN"]
        cash_out_total = keyword_totals[keyword.lower()]["CASH_OUT"]
        print(f"\033[96m{keyword}\033[0m")
        print(f"\033[93mCASH_IN: {cash_in_total:.2f}\033[0m")
        print(f"\033[95mCASH_OUT: {cash_out_total:.2f}\033[0m")
        
        # Special handling for Money Changer - show all times and remarks
        if keyword.lower() == "money changer" and money_changer_times:
            for entry in money_changer_times:
                print(f"\033[94mTime: {entry['time']}, Remark: {entry['remark']}\033[0m")
        
        print("-" * 30)
    
    print(f"\033[92mOutput File: selenium_project/calculated_result.txt\033[0m")
    print(f"\033[92m{'='*50}\033[0m")


def click_next_page(driver, wait_timeout=10):
    try:
        selectors_to_try = [
            # Primary selector for the exact button you showed
            "//li[@title='Next Page' and @class='ant-pagination-next' and @aria-disabled='false']//button[@class='ant-pagination-item-link']",
            # Fallback selectors
            "//li[@title='Next Page' and @aria-disabled='false']//button[@class='ant-pagination-item-link']",
            "//button[@class='ant-pagination-item-link']//span[@aria-label='right']/..",
            "//li[contains(@class,'ant-pagination-next') and @aria-disabled='false']//button"
        ]
        
        next_button = None
        working_selector = None
        
        print("[DEBUG] Searching for Next Page button...")
        
        for selector in selectors_to_try:
            try:
                print(f"[DEBUG] Trying selector: {selector}")
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                working_selector = selector
                print(f"[SUCCESS] Found Next Page button using: {selector}")
                break
            except Exception as e:
                print(f"[DEBUG] Selector failed: {e}")
                continue
        
        if not next_button:
            print("[ERROR] Could not find Next Page button with any selector")
            return False
        
        # Try multiple click strategies
        print(f"[DEBUG] Attempting to click Next Page button...")
        
        # Strategy 1: Regular click
        try:
            next_button.click()
            time.sleep(2)
            print(f"[INFO] Successfully clicked Next Page button")
            return True
        except Exception as e:
            print(f"[DEBUG] Regular click failed: {e}")
        
        # Strategy 2: JavaScript click
        try:
            print("[DEBUG] Trying JavaScript click...")
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
            print(f"[INFO] Successfully clicked Next Page button with JavaScript")
            return True
        except Exception as e:
            print(f"[DEBUG] JavaScript click failed: {e}")
        
        # Strategy 3: Action chains click
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            print("[DEBUG] Trying ActionChains click...")
            ActionChains(driver).move_to_element(next_button).click().perform()
            time.sleep(2)
            print(f"[INFO] Successfully clicked Next Page button with ActionChains")
            return True
        except Exception as e:
            print(f"[DEBUG] ActionChains click failed: {e}")
        
        print("[ERROR] All click strategies failed")
        return False
        
    except Exception as e:
        print(f"[WARNING] Could not click Next Page button: {e}")
        return False


# No duplicate checking needed

def run_optimized_phone_extraction(driver, start_date, end_date):
    """
    Optimized extraction with early stopping based on date range.
    Stops scraping when encountering dates older than start_date.
    """
    page_counter = 1
    all_collected_records = []
    stop_scraping = False
    
    print(f"\033[92m[INFO] Starting optimized phone extraction for date range: {start_date} to {end_date}\033[0m")
    
    while not stop_scraping:
        print(f"\033[92m[INFO] Scraping page {page_counter}...\033[0m")
        
        # Extract data from current page with date filtering
        page_records, should_stop = extract_phone_data_with_date_filter(
            driver, start_date, end_date
        )
        
        # Add all records to collection (no duplicate checking)
        for record in page_records:
            all_collected_records.append(record)
        
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
    print(f"  - Total records collected: {total_records}")
    
    if total_records > 0:
        print_grouped_phone_results(phone_groups)
    else:
        print("\033[93m[WARNING] No phone numbers found in the specified date range.\033[0m")

def show_post_crawl_menu():
    """Show menu after crawling is complete"""
    print("\n" + "="*70)
    print("           CRAWLING COMPLETED - SELECT NEXT ACTION")
    print("="*70)
    print("1. Re-run calculator Script")
    print("2. Exit")
    print("="*70)

    while True:
        try:
            choice = input("Enter your choice (1-2): ").strip()
            if choice == "1":
                print("\n🚀 Starting Add Player Script...")
                print("="*70)
                import subprocess
                subprocess.run(["python", "calculator.py"], check=False)
                return
            elif choice == "2":
                print("\n✅ Exiting...")
                return
            else:
                print("❌ Invalid choice. Please enter 1-2.")
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