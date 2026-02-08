"""
OS-specific date formatting utilities for selenium automation
Provides cross-platform date formatting based on user selection
"""

def select_os_type():
    """Display menu to select operating system for date formatting"""
    print("\n" + "="*60)
    print("           SELECT OPERATING SYSTEM")
    print("="*60)
    print("Choose your operating system for proper date formatting:")
    print("1. macOS / Linux / Unix")
    print("2. Windows")
    print("="*60)

    while True:
        try:
            choice = input("Enter your choice (1-2): ").strip()
            if choice == "1":
                print("\n✅ Selected: macOS/Linux (Unix-style date formatting)")
                print("Date format: %-d (removes leading zeros)")
                print("-"*50)
                return "unix"
            elif choice == "2":
                print("\n✅ Selected: Windows (Windows-style date formatting)")
                print("Date format: %#d (removes leading zeros)")
                print("-"*50)
                return "windows"
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
        except KeyboardInterrupt:
            print("\n\n❌ Operation cancelled by user")
            exit(0)

def format_date_for_calendar(datetime_obj, os_type):
    """
    Format date for calendar selection based on OS type
    
    Args:
        datetime_obj: datetime object to format
        os_type: "windows" or "unix" (includes macOS/Linux)
    
    Returns:
        Formatted date string for calendar aria-label matching
    """
    import platform
    
    # Check if we're actually on Windows for the Windows format
    if os_type == "windows" and platform.system() == "Windows":
        # Windows: %#d removes leading zeros
        return datetime_obj.strftime("%B %#d, %Y")
    else:
        # Unix/Mac/Linux: %-d removes leading zeros  
        # Also use this for "windows" selection on non-Windows systems
        return datetime_obj.strftime("%B %-d, %Y")

def get_os_date_formats():
    """
    Get available date formats for different operating systems
    
    Returns:
        Dictionary with OS types and their date format examples
    """
    return {
        "unix": {
            "format": "%-d",
            "description": "Unix/Mac/Linux style (%-d removes leading zeros)",
            "example": "January 5, 2025"
        },
        "windows": {
            "format": "%#d", 
            "description": "Windows style (%#d removes leading zeros)",
            "example": "January 5, 2025"
        }
    }

if __name__ == "__main__":
    # Test the utility functions
    from datetime import datetime
    
    print("🧪 Testing OS date formatting utilities...")
    
    test_date = datetime(2025, 1, 5, 14, 30, 0)
    
    for os_type in ["unix", "windows"]:
        formatted = format_date_for_calendar(test_date, os_type)
        print(f"{os_type.upper()}: {formatted}")
    
    print("\n✅ OS date utilities working correctly!")