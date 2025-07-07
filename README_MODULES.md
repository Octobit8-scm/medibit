# Medibit Pharmacy Management System - Modular Structure

This document describes the modular structure of the Medibit Pharmacy Management System after refactoring.

## Module Overview

The application has been restructured into separate modules for better organization and maintainability:

### Core Modules

1. **`main.py`** - Application entry point

   - Initializes the database
   - Sets up the application
   - Shows splash screen and main window

2. **`splash_screen.py`** - Splash screen module

   - `MedibitSplashScreen` class
   - Handles application startup display
   - Fallback text-based design if logo not found

3. **`main_window.py`** - Main application window

   - `MainWindow` class
   - Core UI layout and navigation
   - Page management and event handling

4. **`theme.py`** - Theme and styling module

   - `get_stylesheet()` - Returns appropriate stylesheet based on theme
   - `get_dark_stylesheet()` - Dark theme using #D4D4D4 and #2B2B2B colors
   - `get_light_stylesheet()` - Light theme stylesheet

5. **`dialogs.py`** - All dialog classes
   - `AddMedicineDialog` - Add new medicine
   - `EditMedicineDialog` - Edit existing medicine
   - `OrderQuantityDialog` - Set order quantities
   - `NotificationSettingsDialog` - Configure notifications
   - `CustomerInfoDialog` - Customer information
   - `SupplierInfoDialog` - Supplier information
   - `ThresholdSettingDialog` - Set stock thresholds
   - `BulkThresholdDialog` - Bulk threshold management
   - `PharmacyDetailsDialog` - Pharmacy details configuration
   - `QuickAddStockDialog` - Quick stock addition

### Existing Modules (Unchanged)

6. **`db.py`** - Database operations
7. **`config.py`** - Configuration management
8. **`notifications.py`** - Notification system
9. **`barcode_scanner.py`** - Barcode scanning functionality
10. **`receipt_manager.py`** - Receipt generation and management
11. **`order_manager.py`** - Order management
12. **`cloud_storage.py`** - Cloud storage integration

## Benefits of Modular Structure

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Maintainability**: Easier to locate and modify specific functionality
3. **Reusability**: Modules can be reused across different parts of the application
4. **Testing**: Individual modules can be tested in isolation
5. **Collaboration**: Multiple developers can work on different modules simultaneously

## Dark Theme Implementation

The dark theme has been implemented using the specified color combination:

- **Background**: #2B2B2B (Dark gray/black)
- **Foreground/Text**: #D4D4D4 (Light gray)

The theme system automatically switches between light and dark themes based on user preference.

## Usage

To run the application:

```bash
python main.py
```

The application will:

1. Initialize the database
2. Show the splash screen
3. Load the main window with the appropriate theme
4. Display the pharmacy management interface

## File Structure

```
pharmacy/
├── main.py                 # Application entry point
├── splash_screen.py        # Splash screen module
├── main_window.py          # Main window module
├── theme.py               # Theme and styling
├── dialogs.py             # All dialog classes
├── db.py                  # Database operations
├── config.py              # Configuration
├── notifications.py       # Notification system
├── barcode_scanner.py     # Barcode scanning
├── receipt_manager.py     # Receipt management
├── order_manager.py       # Order management
├── cloud_storage.py       # Cloud storage
├── requirements.txt       # Dependencies
├── config.json           # Configuration file
├── notification_config.json # Notification settings
├── medibit.ico           # Application icon
├── logs/                 # Log files directory
├── receipts/             # Generated receipts
└── public/               # Public assets
```

## Migration Notes

The original `ui_main.py` file has been split into multiple modules:

- Splash screen functionality → `splash_screen.py`
- Main window functionality → `main_window.py`
- Dialog classes → `dialogs.py`
- Theme and styling → `theme.py`

All imports and dependencies have been updated to reflect the new structure.

## Future Enhancements

With this modular structure, future enhancements can be easily implemented:

- Add new modules for specific features
- Implement plugin system
- Add unit tests for individual modules
- Create separate UI themes
- Add internationalization support
