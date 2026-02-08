from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from prompt_toolkit import prompt

class DateSelector:
    def __init__(self):
        # Nepal timezone UTC+05:45
        self.nepal_tz = timezone(timedelta(hours=5, minutes=45))
        self.selected_dates = None
    
    def get_nepal_time(self):
        """Get current time in Nepal timezone"""
        return datetime.now(self.nepal_tz)
    
    def format_date(self, date):
        """Format date as YYYY-MM-DD"""
        return date.strftime("%Y-%m-%d")
    
    def get_default_dates(self):
        """Generate default start and end dates"""
        nepal_now = self.get_nepal_time()
        
        # Both start date and end date are today
        today_date = self.format_date(nepal_now)
        
        return today_date, today_date
    
    def get_date_with_default(self, label, default_value):
        """Get date input with pre-filled editable default using prompt_toolkit"""
        return prompt(f"{label}: ", default=default_value).strip()
    
    def terminal_date_selection(self):
        """Terminal-based date selection with pre-filled editable defaults"""
        print("\033[1;33m[INFO] Date Selection (Nepal Time UTC+05:45)\033[0m")
        
        default_start, default_end = self.get_default_dates()
        
        # Start date selection - pre-filled and directly editable
        start_date = self.get_date_with_default("Start Date", default_start)
        
        # End date selection - pre-filled and directly editable  
        end_date = self.get_date_with_default("End Date", default_end)
        
        # Validate dates
        if self.validate_dates(start_date, end_date):
            self.selected_dates = {
                "start_date": start_date,
                "end_date": end_date
            }
            print(f"\033[1;32m[SUCCESS] Date range selected: {start_date} to {end_date}\033[0m")
            return self.selected_dates
        else:
            print("\033[1;31m[ERROR] Invalid date range entered\033[0m")
            return None
    
    def validate_dates(self, start_date, end_date):
        """Validate date format and range"""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Check if start date is before end date
            if start_dt > end_dt:
                print("\033[1;31m[ERROR] Start date must be before end date\033[0m")
                return False
                
            # Check if dates are not in the future (Nepal time)
            nepal_today = self.get_nepal_time().replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if start_dt.replace(tzinfo=self.nepal_tz) > nepal_today:
                print("\033[1;31m[ERROR] Start date cannot be in the future\033[0m")
                return False
                
            if end_dt.replace(tzinfo=self.nepal_tz) > nepal_today:
                print("\033[1;31m[ERROR] End date cannot be in the future\033[0m")
                return False
            
            return True
            
        except ValueError:
            print("\033[1;31m[ERROR] Invalid date format. Use YYYY-MM-DD\033[0m")
            return False
    
    def apply_dates_to_selenium(self, driver, start_date, end_date):
        """Applies the selected dates to the selenium browser"""
        try:
            print(f"\033[1;33m[INFO] Applying dates: {start_date} to {end_date}\033[0m")
            
            # Wait for date input fields to be present
            WebDriverWait(driver, 10)
            
            # Try different selectors for date inputs
            date_selectors = [
                "input[type='date']",
                ".date-picker input",
                "[data-testid='start-date']",
                "[data-testid='end-date']",
                ".start-date input",
                ".end-date input"
            ]
            
            # Find start date field
            start_date_field = None
            for selector in date_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) >= 1:
                        start_date_field = elements[0]
                        break
                except:
                    continue
            
            if start_date_field:
                start_date_field.clear()
                start_date_field.send_keys(start_date)
                print(f"\033[1;32m[SUCCESS] Start date applied: {start_date}\033[0m")
            else:
                print("\033[1;31m[WARNING] Could not find start date field\033[0m")
            
            # Find end date field
            end_date_field = None
            for selector in date_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) >= 2:
                        end_date_field = elements[1]
                        break
                    elif len(elements) == 1 and start_date_field != elements[0]:
                        end_date_field = elements[0]
                        break
                except:
                    continue
            
            if end_date_field:
                end_date_field.clear()
                end_date_field.send_keys(end_date)
                print(f"\033[1;32m[SUCCESS] End date applied: {end_date}\033[0m")
            else:
                print("\033[1;31m[WARNING] Could not find end date field\033[0m")
            
            return True
            
        except Exception as e:
            print(f"\033[1;31m[ERROR] Failed to apply dates: {e}\033[0m")
            return False

def get_date_selection():
    """Main function to get date selection from user via terminal"""
    selector = DateSelector()
    dates = selector.terminal_date_selection()
    
    if dates:
        # Convert string dates to date objects for comparison
        try:
            start_date = datetime.strptime(dates["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(dates["end_date"], "%Y-%m-%d").date()
            return start_date, end_date
        except ValueError as e:
            print(f"\033[1;31m[ERROR] Invalid date format: {e}\033[0m")
            return None, None
    else:
        return None, None