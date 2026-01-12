#!/usr/bin/env python3
"""
Telegram Keyword Automation Tool
================================
This tool monitors your clipboard for keywords copied from Telegram,
then automates pasting and submitting to a target website.

Requirements:
- Python 3.8+
- pip install pyautogui pyperclip selenium webdriver-manager

Usage:
1. Configure settings below
2. Run: python telegram_automation.py
3. Copy text containing your keyword from Telegram
4. The automation will start automatically
"""

import time
import threading
import sys
from datetime import datetime

try:
    import pyautogui
    import pyperclip
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("\nPlease install required packages:")
    print("pip install pyautogui pyperclip selenium webdriver-manager")
    sys.exit(1)

# ============================================
# CONFIGURATION - Edit these settings
# ============================================

CONFIG = {
    # The keyword to filter for in copied text
    "keyword_filter": "PROMO",
    
    # Target website URL
    "target_url": "https://example.com/search",
    
    # CSS selector for the input field (leave empty to use active element)
    "input_selector": "input[type='text']",
    
    # Interval between Enter key presses (in seconds)
    "spam_interval_seconds": 2,
    
    # Page reset interval (in minutes)
    "reset_interval_minutes": 15,
    
    # Show browser window (False = headless/hidden)
    "show_browser": True,
}

# ============================================
# AUTOMATION ENGINE
# ============================================

class TelegramAutomation:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.is_running = False
        self.last_clipboard = ""
        self.current_keyword = None
        self.spam_thread = None
        self.reset_thread = None
        self.start_time = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def start_browser(self):
        """Initialize the Chrome browser"""
        try:
            options = Options()
            if not self.config["show_browser"]:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.get(self.config["target_url"])
            self.log(f"Browser opened: {self.config['target_url']}")
            return True
        except Exception as e:
            self.log(f"Failed to start browser: {e}", "ERROR")
            return False
    
    def type_keyword(self, keyword):
        """Type the keyword into the target input field"""
        try:
            if self.config["input_selector"]:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, self.config["input_selector"]))
                    )
                    element.clear()
                    element.send_keys(keyword)
                except:
                    # Fallback: just type into active element
                    active = self.driver.switch_to.active_element
                    active.send_keys(keyword)
            else:
                active = self.driver.switch_to.active_element
                active.send_keys(keyword)
            
            self.log(f"Typed keyword: {keyword}")
            return True
        except Exception as e:
            self.log(f"Failed to type keyword: {e}", "ERROR")
            return False
    
    def press_enter(self):
        """Press Enter key"""
        try:
            active = self.driver.switch_to.active_element
            active.send_keys(Keys.RETURN)
            return True
        except Exception as e:
            self.log(f"Failed to press Enter: {e}", "ERROR")
            return False
    
    def spam_loop(self):
        """Continuously press Enter at configured interval"""
        while self.is_running:
            if self.driver:
                self.press_enter()
            time.sleep(self.config["spam_interval_seconds"])
    
    def reset_loop(self):
        """Reset the page at configured interval"""
        reset_seconds = self.config["reset_interval_minutes"] * 60
        while self.is_running:
            time.sleep(reset_seconds)
            if self.is_running and self.driver:
                self.log("Resetting page...")
                try:
                    self.driver.refresh()
                    time.sleep(2)  # Wait for page load
                    if self.current_keyword:
                        self.type_keyword(self.current_keyword)
                except Exception as e:
                    self.log(f"Reset failed: {e}", "ERROR")
    
    def start_automation(self, keyword):
        """Start the automation with the given keyword"""
        if self.is_running:
            self.stop_automation()
        
        self.current_keyword = keyword
        self.is_running = True
        self.start_time = datetime.now()
        
        self.log(f"Starting automation for keyword: {keyword}")
        
        # Start browser
        if not self.start_browser():
            self.is_running = False
            return False
        
        # Type initial keyword
        time.sleep(1)
        self.type_keyword(keyword)
        
        # Start spam thread
        self.spam_thread = threading.Thread(target=self.spam_loop, daemon=True)
        self.spam_thread.start()
        
        # Start reset thread
        self.reset_thread = threading.Thread(target=self.reset_loop, daemon=True)
        self.reset_thread.start()
        
        self.log("Automation started! Press Ctrl+C to stop.")
        return True
    
    def stop_automation(self):
        """Stop the automation"""
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        self.log("Automation stopped")
    
    def check_clipboard(self):
        """Check clipboard for keyword"""
        try:
            current = pyperclip.paste()
            if current != self.last_clipboard:
                self.last_clipboard = current
                keyword_filter = self.config["keyword_filter"]
                if keyword_filter.lower() in current.lower():
                    self.log(f"Keyword detected in clipboard: '{current[:100]}...'")
                    # Use the ACTUAL copied text from clipboard, not just the filter
                    # This pastes exactly what the user copied from Telegram
                    self.start_automation(current.strip())
        except Exception as e:
            pass  # Clipboard access might fail sometimes
    
    def run(self):
        """Main loop - monitor clipboard"""
        self.log("=" * 50)
        self.log("TELEGRAM AUTOMATION TOOL")
        self.log("=" * 50)
        self.log(f"Keyword filter: {self.config['keyword_filter']}")
        self.log(f"Target URL: {self.config['target_url']}")
        self.log(f"Spam interval: {self.config['spam_interval_seconds']}s")
        self.log(f"Reset interval: {self.config['reset_interval_minutes']}m")
        self.log("=" * 50)
        self.log("Monitoring clipboard... Copy text from Telegram containing your keyword!")
        self.log("Press Ctrl+C to exit")
        self.log("")
        
        try:
            while True:
                self.check_clipboard()
                time.sleep(0.5)  # Check every 500ms
        except KeyboardInterrupt:
            self.log("\nShutting down...")
            self.stop_automation()
            self.log("Goodbye!")


# ============================================
# GUI VERSION (Optional)
# ============================================

def run_gui():
    """Run with a simple GUI for configuration"""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("tkinter not available, running in CLI mode")
        return False
    
    class AutomationGUI:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Telegram Automation Tool")
            self.root.geometry("500x600")
            self.root.configure(bg="#1a1a2e")
            
            self.automation = None
            self.monitoring = False
            
            self.setup_ui()
        
        def setup_ui(self):
            # Style
            style = ttk.Style()
            style.configure("Dark.TFrame", background="#1a1a2e")
            style.configure("Dark.TLabel", background="#1a1a2e", foreground="#00ffff", font=("Consolas", 10))
            style.configure("Dark.TEntry", fieldbackground="#16213e", foreground="white")
            style.configure("Dark.TButton", background="#00ffff", foreground="#1a1a2e")
            
            # Main frame
            main = tk.Frame(self.root, bg="#1a1a2e", padx=20, pady=20)
            main.pack(fill="both", expand=True)
            
            # Title
            title = tk.Label(main, text="TELEGRAM AUTOMATION", font=("Consolas", 16, "bold"), 
                           bg="#1a1a2e", fg="#00ffff")
            title.pack(pady=(0, 20))
            
            # Keyword
            tk.Label(main, text="Keyword Filter:", bg="#1a1a2e", fg="#00ffff", 
                    font=("Consolas", 10)).pack(anchor="w")
            self.keyword_entry = tk.Entry(main, bg="#16213e", fg="white", 
                                         insertbackground="white", font=("Consolas", 11))
            self.keyword_entry.pack(fill="x", pady=(0, 10))
            self.keyword_entry.insert(0, "PROMO")
            
            # Target URL
            tk.Label(main, text="Target Website URL:", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.url_entry = tk.Entry(main, bg="#16213e", fg="white",
                                     insertbackground="white", font=("Consolas", 11))
            self.url_entry.pack(fill="x", pady=(0, 10))
            self.url_entry.insert(0, "https://example.com/search")
            
            # Input selector
            tk.Label(main, text="Input Selector (CSS):", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.selector_entry = tk.Entry(main, bg="#16213e", fg="white",
                                          insertbackground="white", font=("Consolas", 11))
            self.selector_entry.pack(fill="x", pady=(0, 10))
            self.selector_entry.insert(0, "input[type='text']")
            
            # Spam interval
            tk.Label(main, text="Spam Interval (seconds):", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.interval_entry = tk.Entry(main, bg="#16213e", fg="white",
                                          insertbackground="white", font=("Consolas", 11))
            self.interval_entry.pack(fill="x", pady=(0, 10))
            self.interval_entry.insert(0, "2")
            
            # Reset interval
            tk.Label(main, text="Reset Interval (minutes):", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.reset_entry = tk.Entry(main, bg="#16213e", fg="white",
                                       insertbackground="white", font=("Consolas", 11))
            self.reset_entry.pack(fill="x", pady=(0, 10))
            self.reset_entry.insert(0, "15")
            
            # Show browser checkbox
            self.show_browser_var = tk.BooleanVar(value=True)
            tk.Checkbutton(main, text="Show Browser Window", variable=self.show_browser_var,
                          bg="#1a1a2e", fg="#00ffff", selectcolor="#16213e",
                          activebackground="#1a1a2e", activeforeground="#00ffff",
                          font=("Consolas", 10)).pack(anchor="w", pady=(0, 20))
            
            # Buttons
            btn_frame = tk.Frame(main, bg="#1a1a2e")
            btn_frame.pack(fill="x", pady=10)
            
            self.start_btn = tk.Button(btn_frame, text="START MONITORING", 
                                       command=self.toggle_monitoring,
                                       bg="#00ffff", fg="#1a1a2e", font=("Consolas", 11, "bold"),
                                       activebackground="#00cccc", cursor="hand2")
            self.start_btn.pack(fill="x", pady=5)
            
            # Status
            self.status_label = tk.Label(main, text="Status: Idle", 
                                        bg="#1a1a2e", fg="#888888", font=("Consolas", 10))
            self.status_label.pack(pady=10)
            
            # Log area
            tk.Label(main, text="Logs:", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            
            self.log_text = tk.Text(main, bg="#16213e", fg="#00ff00", height=10,
                                   font=("Consolas", 9), insertbackground="white")
            self.log_text.pack(fill="both", expand=True)
            
            # Instructions
            instructions = tk.Label(main, 
                text="Copy text from Telegram containing your keyword to trigger automation",
                bg="#1a1a2e", fg="#666666", font=("Consolas", 9), wraplength=450)
            instructions.pack(pady=10)
        
        def log(self, message):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
        
        def toggle_monitoring(self):
            if not self.monitoring:
                self.start_monitoring()
            else:
                self.stop_monitoring()
        
        def start_monitoring(self):
            config = {
                "keyword_filter": self.keyword_entry.get(),
                "target_url": self.url_entry.get(),
                "input_selector": self.selector_entry.get(),
                "spam_interval_seconds": int(self.interval_entry.get()),
                "reset_interval_minutes": int(self.reset_entry.get()),
                "show_browser": self.show_browser_var.get(),
            }
            
            self.automation = TelegramAutomation(config)
            self.automation.log = self.log  # Redirect logs to GUI
            
            self.monitoring = True
            self.start_btn.configure(text="STOP MONITORING", bg="#ff4444")
            self.status_label.configure(text="Status: Monitoring clipboard...", fg="#00ff00")
            self.log("Started monitoring clipboard for keyword: " + config["keyword_filter"])
            
            # Start clipboard monitoring in background
            self.check_clipboard_loop()
        
        def stop_monitoring(self):
            self.monitoring = False
            if self.automation:
                self.automation.stop_automation()
            self.start_btn.configure(text="START MONITORING", bg="#00ffff")
            self.status_label.configure(text="Status: Stopped", fg="#888888")
            self.log("Monitoring stopped")
        
        def check_clipboard_loop(self):
            if self.monitoring and self.automation:
                self.automation.check_clipboard()
                self.root.after(500, self.check_clipboard_loop)
        
        def run(self):
            self.root.mainloop()
    
    app = AutomationGUI()
    app.run()
    return True


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    print("Telegram Automation Tool")
    print("========================")
    
    # Try GUI first, fall back to CLI
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        automation = TelegramAutomation(CONFIG)
        automation.run()
    else:
        if not run_gui():
            automation = TelegramAutomation(CONFIG)
            automation.run()
