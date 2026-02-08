"""
Terminal utility functions for Selenium automation scripts
Provides terminal clearing, customization, and display functions
"""
import os
import sys
import platform

def clear_terminal():
    """Clear the terminal screen across different operating systems"""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def set_terminal_title(title):
    """Set the terminal window title"""
    if platform.system() == "Windows":
        os.system(f'title {title}')
    else:
        sys.stdout.write(f'\033]0;{title}\007')
        sys.stdout.flush()

def print_header(title, subtitle=""):
    """Print a formatted header for the automation"""
    clear_terminal()
    print("=" * 60)
    print(f"           {title}")
    if subtitle:
        print(f"           {subtitle}")
    print("=" * 60)
    print()

def print_status(message, status_type="INFO"):
    """Print colored status messages"""
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"     # Reset
    }

    color = colors.get(status_type, colors["INFO"])
    reset = colors["RESET"]

    print(f"{color}[{status_type}] {message}{reset}")

def setup_automation_terminal(script_name):
    """Setup terminal for automation with proper title and header"""
    set_terminal_title(f"Selenium Automation - {script_name}")
    print_header("SELENIUM AUTOMATION", f"Running: {script_name}")

def cleanup_terminal():
    """Clean up terminal at the end of automation"""
    print()
    print("=" * 60)
    print("           AUTOMATION COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    # Test the terminal utilities
    setup_automation_terminal("Test Script")
    print_status("This is an info message", "INFO")
    print_status("This is a success message", "SUCCESS")
    print_status("This is a warning message", "WARNING")
    print_status("This is an error message", "ERROR")
    cleanup_terminal()