from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
from selenium.webdriver.support.ui import Select
from datetime import datetime
from collections import defaultdict
import re
from selenium.webdriver import ActionChains
from selenium.common.exceptions import TimeoutException



def wait_for_overlay_to_disappear(driver, max_wait=5):
    """Fast overlay detection - only wait if overlay actually exists"""
    overlay_selectors = [
        "div.absolute.inset-0.transition-opacity.duration-300.bg-slate-900\\/60",
        ".app-preloader",
        "div.app-preloader"
    ]
    
    overlay_found = False
    for selector in overlay_selectors:
        try:
            # Quick check if overlay exists
            overlays = driver.find_elements(By.CSS_SELECTOR, selector)
            if overlays and overlays[0].is_displayed():
                print(f"[INFO] {selector} overlay detected, waiting...")
                WebDriverWait(driver, max_wait).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                )
                overlay_found = True
                print(f"[INFO] {selector} overlay disappeared")
        except:
            continue
    
    if overlay_found:
        time.sleep(0.3)  # Brief wait for DOM stability
        return True
    return False


def smart_click(element, verify_callback=None):
    """
    Smart click with minimal retries - only retry if overlay blocks
    """
    try:
        # Try normal click first
        element.click()
        
        # Quick verification if callback provided
        if verify_callback:
            time.sleep(0.3)
            if verify_callback():
                return True
            else:
                # Only retry if overlay is blocking
                if wait_for_overlay_to_disappear(driver, max_wait=3):
                    element.click()
                    time.sleep(0.3)
                    return verify_callback()
                return False
        return True
        
    except Exception as click_error:
        error_msg = str(click_error)
        # Only retry if it's an overlay blocking issue
        if "obscures it" in error_msg or "not clickable" in error_msg:
            print("[INFO] Overlay blocking click, trying JS click...")
            if wait_for_overlay_to_disappear(driver, max_wait=3):
                try:
                    driver.execute_script("arguments[0].click();", element)
                    if verify_callback:
                        time.sleep(0.3)
                        return verify_callback()
                    return True
                except Exception as js_click_error:
                    print(f"[INFO] JS click also failed: {js_click_error}")
                    print("[INFO] Pressing Enter to dismiss modal/overlay...")
                    element.send_keys(Keys.ENTER)
                    time.sleep(0.5)
                    if verify_callback:
                        return verify_callback()
                    return True
        raise click_error


def reliable_click_with_locator(locator, max_attempts=3, delay=1, verify_callback=None):
    """
    Click element using locator to handle stale elements
    """
    for attempt in range(max_attempts):
        try:
            print(f"[INFO] Attempting click with locator (attempt {attempt + 1}/{max_attempts})")
            
            # Wait for any overlays to disappear
            wait_for_overlay_to_disappear(driver, max_wait=3)
            
            # Re-find element to avoid stale reference
            element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(locator)
            )
            
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            
            # Try normal click first
            try:
                element.click()
                print("[INFO] Normal click successful")
            except Exception as click_error:
                print(f"[WARN] Normal click failed: {click_error}")
                # Fallback to JavaScript click
                print("[INFO] Trying JavaScript click...")
                driver.execute_script("arguments[0].click();", element)
                print("[INFO] JavaScript click successful")
            
            time.sleep(0.5)
            
            # If verification callback provided, use it
            if verify_callback and not verify_callback():
                if attempt < max_attempts - 1:
                    print(f"[WARN] Click verification failed, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    print("[ERROR] Click verification failed after all attempts")
                    return False
            
            print("[INFO] Click successful")
            return True
            
        except Exception as e:
            print(f"[WARN] Click attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"[ERROR] All click attempts failed: {e}")
                raise e
    return False

def check_player_id_toast(driver, timeout=10):
    """
    Waits up to `timeout` seconds to see if the 'player id field is required' toast appears.
    Prints log if found, returns True/False.
    """
    try:
        toast = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'toastify') and contains(text(), 'The player id field is required.')]")
            )
        )
        print("[LOG] Toast appeared: Player ID field is required.")
        return True
    except TimeoutException:
        return False
    
def click_bank_transactions_link(driver, timeout=5):
    """
    Waits up to `timeout` seconds for the bank transactions link to appear,
    then clicks it. Returns True if clicked, False otherwise.
    """
    try:
        link = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@href='https://www.rocketgo.asia/op/bank-transactions']")
            )
        )
        link.click()
        print("[LOG] Clicked Bank Transactions link.")
        return True
    except TimeoutException:
        print("[LOG] Bank Transactions link not found within timeout.")
        return False

def reliable_click(element, max_attempts=3, delay=1, verify_callback=None):
    """
    Click element with retry mechanism, overlay handling, and stale element recovery
    """
    for attempt in range(max_attempts):
        try:
            print(f"[INFO] Attempting click (attempt {attempt + 1}/{max_attempts})")
            
            # Wait for any overlays to disappear
            wait_for_overlay_to_disappear(driver, max_wait=3)
            
            # Scroll element into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            
            # Try normal click first
            try:
                element.click()
                print("[INFO] Normal click successful")
            except Exception as click_error:
                print(f"[WARN] Normal click failed: {click_error}")
                # Fallback to JavaScript click
                print("[INFO] Trying JavaScript click...")
                driver.execute_script("arguments[0].click();", element)
                print("[INFO] JavaScript click successful")
            
            time.sleep(0.5)
            
            # If verification callback provided, use it
            if verify_callback and not verify_callback():
                if attempt < max_attempts - 1:
                    print(f"[WARN] Click verification failed, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    print("[ERROR] Click verification failed after all attempts")
                    return False
            
            print("[INFO] Click successful")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"[WARN] Click attempt {attempt + 1} failed: {e}")
            
            # Check if it's a stale element error
            if "stale" in error_msg.lower() or "not connected to the DOM" in error_msg:
                print("[WARN] Stale element detected - element needs to be re-found")
                
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"[ERROR] All click attempts failed: {e}")
                raise e
    return False


def verify_dropdown_opened(driver):
    """Verify dropdown is opened by checking for dropdown options"""
    try:
        dropdown_options = driver.find_elements(By.CSS_SELECTOR, ".ts-dropdown, .dropdown-menu, [role='listbox']")
        return len(dropdown_options) > 0
    except:
        return False


def verify_modal_opened(driver):
    """Verify modal/popup window is opened"""
    try:
        modal = driver.find_elements(By.CSS_SELECTOR, ".flex.justify-between.px-4.py-3.rounded-t-lg.bg-slate-200.dark\\:bg-navy-800.sm\\:px-5")
        return len(modal) > 0 and modal[0].is_displayed()
    except:
        return False


def verify_calendar_opened(driver):
    """Verify calendar popup is opened"""
    try:
        calendar = driver.find_elements(By.CLASS_NAME, "flatpickr-calendar")
        return len(calendar) > 0 and "open" in calendar[0].get_attribute("class")
    except:
        return False





profile_path = "/Users/admin/Library/Application Support/Firefox/Profiles/7oz304au.default-release"
firefox_profile = webdriver.FirefoxProfile(profile_path)

options = Options()
options.set_preference("profile", profile_path)
# Optional: Use a separate Firefox profile
# Replace 'selenium-profile' with the name of a Firefox profile you’ve created
# or comment out if you want a fresh profile every time
# options.profile = "/Users/admin/Library/Application Support/Firefox/Profiles/xxxxxxxx.selenium-profile"

# Headless mode if needed
# options.add_argument('--headless')

# Setup the driver
service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)
driver.maximize_window()



driver.get("https://www.rocketgo.asia/login")

wait = WebDriverWait(driver, 40)
merchant_input = wait.until(EC.presence_of_element_located((By.NAME, "merchant_code")))
merchant_input.send_keys("luckytaj")

wait = WebDriverWait(driver, 40)
username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
username_input.send_keys("Admin_Json")

wait = WebDriverWait(driver, 40)
password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
password_input.send_keys("json8888"+ Keys.ENTER)

time.sleep(3)

click_bank_transactions_link(driver)
wait_for_overlay_to_disappear(driver, max_wait=5)


def remove_bom(line):
    BOM = '\ufeff'
    if line.startswith(BOM):
        return line.lstrip(BOM)
    return line





def gateway_setup_movement(gateway_name):
    print(f"\033[93m[Gateway Setup] Executing setup for {gateway_name}\033[0m")

    gateway_map = {
        "XYPAY": "XYPAY",
        "XCPAY": "XCPAY",
        "SKPAY": "SKPAY",
        "YTPAY": "YTPAY",
        "OSPAY": "OSPAY",
        "SIMPLYPAY": "SIMPLYPAY",
        "VADERPAY": "VADERPAY",
        "PASSPAY": "PASSPAY",
        "MULTIPAY": "MULTIPAY",
        "U9PAY": "U9PAY",
        "BOMBAYPAY": "BOMBAYPAY",
        "EPAY": "EPAY",
        "MOHAMMED AMEER ABBAS": "Karnataka Bank 2",
        "Test": "Test",
        "Test2" : "Test2",
        "BOPAY": "BOPAY",
        "CPUPAY": "CPUPAY"
    }

    if gateway_name in gateway_map:
        enter_gateway_name(gateway_map[gateway_name])



def enter_gateway_name(gateway_text):
    # Step 1: Wait for preloader to disappear
    WebDriverWait(driver, 30).until(
        EC.invisibility_of_element_located((By.CLASS_NAME, "app-preloader"))
    )

    # Step 2: Click container to open dropdown using locator-based approach
    time.sleep(0.5)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)  # Optional: wait for any sticky headers to settle
    
    # Click dropdown container to open it
    container = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.ts-control"))
    )
    smart_click(container, verify_callback=lambda: verify_dropdown_opened(driver))
    time.sleep(0.5)

    # Step 3: Find actual input (not always interactable)
    gateway_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "selectBank-ts-control"))
    )

    # Optional: Scroll it into view
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", gateway_input)
    time.sleep(0.3)

    print("Displayed:", gateway_input.is_displayed())
    print("Enabled:", gateway_input.is_enabled())
    print("Size:", gateway_input.size)
    print("Location:", gateway_input.location)

    try:
        # Try normal input method first
        gateway_input.send_keys(gateway_text)
    except Exception as e:
        print(f"[WARN] Normal input failed, using JS. Reason: {e}")
        # Fallback to JS-based input
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        """, gateway_input, gateway_text)

    time.sleep(2)  # Wait for dropdown options

    # Step 4: Check if dropdown has valid options before selection
    try:
        # Check for dropdown options
        dropdown_options = driver.find_elements(By.CSS_SELECTOR, ".ts-dropdown .option, .ts-dropdown-content .option, [data-selectable='true'], .dropdown-item")
        
        if len(dropdown_options) == 0:
            print("[WARN] No dropdown options found, checking for alternative selectors...")
            # Try alternative selectors for dropdown options
            alternative_selectors = [
                ".ts-dropdown [data-value]",
                ".dropdown-menu li",
                ".select-dropdown li",
                "[role='option']",
                ".ts-dropdown > div"
            ]
            
            for selector in alternative_selectors:
                dropdown_options = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(dropdown_options) > 0:
                    print(f"[INFO] Found {len(dropdown_options)} options with selector: {selector}")
                    break
        
        if len(dropdown_options) > 0:
            print(f"[INFO] Found {len(dropdown_options)} dropdown options")
            # Press Enter to select the first matching option
            gateway_input.send_keys(Keys.ENTER)
            print(f"[INFO] Gateway '{gateway_text}' entered and selected.")
        else:
            print("[WARN] No dropdown options available - the dropdown might be undefined/empty")
            print("[INFO] Trying to proceed without selection...")
            # Try pressing Enter anyway in case the input is accepted
            gateway_input.send_keys(Keys.ENTER)
            print(f"[INFO] Attempted to enter '{gateway_text}' without dropdown options.")
            
    except Exception as e:
        print(f"[WARN] Error checking dropdown options: {e}")
        # Fallback - try pressing Enter anyway
        gateway_input.send_keys(Keys.ENTER)
        print(f"[INFO] Fallback: Attempted to enter '{gateway_text}'.")
    
    time.sleep(0.5)





    # --- Check Table load with multiple selectors ---
    print("[INFO] Waiting for table to load...")
    table_selectors = [
        (By.CLASS_NAME, "gridjs-wrapper"),
        (By.CSS_SELECTOR, ".gridjs-wrapper"),
        (By.CSS_SELECTOR, "table"),
        (By.CSS_SELECTOR, ".table"),
        (By.CSS_SELECTOR, "[role='table']"),
        (By.CSS_SELECTOR, ".data-table"),
        (By.CSS_SELECTOR, ".grid-table")
    ]
    
    table_loaded = False
    wait = WebDriverWait(driver, 45)  # Increased timeout
    
    for selector in table_selectors:
        try:
            wait.until(EC.presence_of_element_located(selector))
            print(f"[INFO] Table loaded with selector: {selector}")
            table_loaded = True
            break
        except Exception as e:
            print(f"[DEBUG] Table selector {selector} failed: {e}")
            continue
    
    if not table_loaded:
        print("[WARN] Table loading timeout - proceeding anyway")
    
    time.sleep(2)  # Additional wait for table content to populate



# ======== Add Details HERE =======


def add_transaction_details(record):

    """Fill Order ID, Phone Number, and Amount into form."""
    print(f"Processing Record: {record}")

    # Wait briefly for page load
    time.sleep(1)
    
    # Find Add button quickly
    wait = WebDriverWait(driver, 20)
    add_button = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[contains(text(), 'Add New Bank Transaction')]"
    )))
    
    # Single smart click with modal verification
    smart_click(add_button, verify_callback=lambda: verify_modal_opened(driver))
    print("[INFO] Add Transaction button clicked")

    # === Wait for the window UI to appear ===
    WebDriverWait(driver, 20, poll_frequency=0.2).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR, ".flex.justify-between.px-4.py-3.rounded-t-lg.bg-slate-200.dark\\:bg-navy-800.sm\\:px-5"
        ))
    )
    print("[INFO] Target Window element appeared — proceeding...")

    # ===== Order ID =====
    order_id_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Bank Reference']"))
    )

    # Force scroll into view before clear and type
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", order_id_input)
    time.sleep(0.3)

    order_id_input.clear()
    order_id_input.send_keys(record["Order ID"])
    print(f"[INFO] Order ID entered: {record['Order ID']}")


    # ===== Phone Number =====

    phone_number_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Player ID']"))
    )
    phone_number_input.clear()
    phone_number_input.send_keys(record["Phone Number"])
    print(f"[INFO] Order ID entered: {record['Phone Number']}")



    # ===== Amount =====

    amount_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='amount']"))
    )
    amount_input.clear()
    amount_input.send_keys(str(record["Amount"]).replace(",", ""))
    print(f"[INFO] Order ID entered: {record['Amount']}")


    # ===== Datepicker =====

    calendar_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Choose datetime...']"))
    )
    
    # Use smart click with calendar verification
    smart_click(calendar_input, verify_callback=lambda: verify_calendar_opened(driver))
    print(f"[INFO] Calendar input clicked...")

    calendar_popup = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flatpickr-calendar"))
    )

    if "open" in calendar_popup.get_attribute("class"):
        print("[INFO] Calendar popup is OPEN")

        target_date = record["Datetime"].strftime("%B %-d, %Y")  # e.g. "July 6, 2025"
        all_days = driver.find_elements(By.CSS_SELECTOR, ".flatpickr-day")

        for day in all_days:
            if day.get_attribute("aria-label") == target_date:
                driver.execute_script("arguments[0].scrollIntoView(true);", day)
                # Use smart click for date selection
                smart_click(day)
                print(f"[INFO] Clicked date: {target_date}")
                break
        else:
            print(f"[ERROR] Date '{target_date}' not found in picker.")

    else:
        print("[WARN] Calendar popup did NOT open")


    # ===== Hour =====
    wait = WebDriverWait(driver, 40)
    merchant_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.flatpickr-hour")))
    merchant_input.clear()
    merchant_input.send_keys(record["Hour"])

    time.sleep(.5)


    # ===== Minutes =====
    wait = WebDriverWait(driver, 40)
    merchant_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.flatpickr-minute")))
    merchant_input.clear()
    merchant_input.send_keys(record["Minute"])

    time.sleep(.5)


    # ===== Decide AM or PM from the record =====

    ampm_target = "AM" if int(record.get("Hour", 0)) < 12 else "PM"
    ampm_toggle = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "flatpickr-am-pm"))
    )

    # Check and click if needed
    current_ampm = ampm_toggle.text.strip().upper()
    if current_ampm != ampm_target:
        # Use smart click for AM/PM toggle
        smart_click(ampm_toggle)
        print(f"[INFO] AM/PM toggled to {ampm_target}")
    else:
        print(f"[INFO] AM/PM already set to {ampm_target}")

    time.sleep(1)
    
    # Select Player ID field (do nothing with it)
    player_id_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Player ID']"))
    )
    player_id_input.click()

    time.sleep(1)
    
    # Confirm calendar selection by pressing Enter on the calendar input or body
    try:
        # First try to press Enter on the calendar input to confirm the datetime selection
        calendar_input = driver.find_element(By.XPATH, "//input[@placeholder='Choose datetime...']")
        calendar_input.send_keys(Keys.ENTER)
        print("[INFO] Calendar selection confirmed via Enter on calendar input")
    except Exception as e:
        print(f"[WARN] Could not confirm calendar via input: {e}")
        # Fallback: press Enter on body to confirm calendar
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ENTER)
            print("[INFO] Calendar selection confirmed via Enter on body")
        except Exception as e2:
            print(f"[WARN] Could not confirm calendar: {e2}")
    
    time.sleep(0.5)
    
    # Check for player ID toast after form submission
    if check_player_id_toast(driver):
        print("\033[91m[WARN]\033[0m Player ID field validation failed - form not submitted")
        
        # Try pressing Enter up to 3 times with 2s interval
        for attempt in range(5):
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.ENTER)
                print(f"[INFO] Sent ENTER key to dismiss toast (attempt {attempt+1}/3)")
                time.sleep(3)
            except Exception as e:
                print(f"[ERROR] Could not send ENTER key: {e}")
    else:
        print("[INFO] No player ID toast detected - form submission successful")


    time.sleep(0.5)










def parse_and_execute(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_gateway = None
    current_records = []
    performed_gateways = set()

    supported_gateways = {
        "XYPAY", "SKPAY", "YTPAY", "OSPAY", "SIMPLYPAY", "VADERPAY",
        "PASSPAY", "MULTIPAY", "U9PAY", "BOMBAYPAY", "EPAY", 
        "MOHAMMED AMEER ABBAS", "Test", "Test2", "XCPAY", "BOPAY", "CPUPAY"
    }

    # Temporary variables for one record
    order_id = phone = amount = time_str = None
    dt = hour_str = minute_str = None

    for raw_line in lines:
        line = remove_bom(raw_line.strip())

        if not line:
            continue

        # Stop condition — flush records first
        if line.startswith("==== GRAND TOTAL for All Gateways:"):
            print("[INFO] Reached GRAND TOTAL line. Stopping processing.")
            break

        # Detect gateway header line
        if line.startswith("====") and "Total Amount" in line:
            if current_records:
                print(f"[DEBUG] Flushing {len(current_records)} records under gateway '{current_gateway}'")
                for record in current_records:
                    add_transaction_details(record)
            current_records = []

            match = re.match(r"==== (.*?) \(", line)
            if match:
                detected_gateway = match.group(1)
                if detected_gateway in supported_gateways:
                    current_gateway = detected_gateway
                    if current_gateway not in performed_gateways:
                        gateway_setup_movement(current_gateway)
                        performed_gateways.add(current_gateway)
                else:
                    print(f"[WARNING] Unsupported gateway '{detected_gateway}', skipping records.")
                    current_gateway = None
            continue

        # Skip if gateway not set
        if not current_gateway:
            continue

        # Parse record fields
        if line.startswith("Order ID:"):
            order_id = line.split(":", 1)[1].strip()
        elif line.startswith("Phone Number:"):
            phone = line.split(":", 1)[1].strip()
        elif line.startswith("Amount:"):
            amount = line.split(":", 1)[1].strip()
        elif line.startswith("Time:"):
            time_str = line.split(":", 1)[1].strip()
            try:
                dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                hour_str = f"{dt.hour:02d}"
                minute_str = f"{dt.minute:02d}"

                # ✅ Only append once all fields are known
                if all([order_id, phone, amount, time_str]):
                    current_records.append({
                        "Order ID": order_id,
                        "Phone Number": phone,
                        "Amount": amount,
                        "Time": time_str,
                        "Hour": hour_str,
                        "Minute": minute_str,
                        "Datetime": dt
                    })
                    # Reset vars for next record
                    order_id = phone = amount = time_str = None
                    dt = hour_str = minute_str = None
            except ValueError:
                print(f"[ERROR] Invalid datetime: {time_str}")
                continue

    # ✅ Final flush at EOF
    if current_records:
        print(f"[DEBUG] Final flush: {len(current_records)} records under gateway '{current_gateway}'")
        for record in current_records:
            add_transaction_details(record)



# ===== Function call HERE =====
parse_and_execute("selenium_project/selenium-transaction_history.txt")
time.sleep(2)  
driver.quit()