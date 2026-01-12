#!/usr/bin/env python3
"""
Telegram Code Scanner with Auto-Spam
=====================================
1. Scans Telegram for codes in images
2. Pastes code to website
3. Continuously presses Enter (spam)
4. Resets page periodically
5. Press HOME key to select screen region
"""
import time
import threading
import sys
import os
import re
from datetime import datetime
try:
    import pyautogui
    import pyperclip
    from PIL import Image, ImageGrab, ImageEnhance
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"Missing: {e}")
    sys.exit(1)
try:
    import pytesseract
except ImportError:
    pytesseract = None
try:
    import keyboard
except ImportError:
    keyboard = None
class TelegramCodeScanner:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.is_running = False
        self.is_spamming = False
        self.last_code = ""
        self.current_code = ""
        self.capture_region = None
        
        self.scan_thread = None
        self.spam_thread = None
        self.reset_thread = None
        
        if pytesseract:
            tess_path = config.get("tesseract_path", "")
            if os.path.exists(tess_path):
                pytesseract.pytesseract.tesseract_cmd = tess_path
            else:
                for path in [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        break
    
    def log(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def start_browser(self):
        try:
            options = Options()
            if not self.config.get("show_browser", True):
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.get(self.config["target_url"])
            self.log(f"Browser opened: {self.config['target_url']}")
            return True
        except Exception as e:
            self.log(f"Browser error: {e}")
            return False
    
    def extract_code(self, image):
        if not pytesseract:
            return None
        try:
            gray = image.convert('L')
            enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
            text = pytesseract.image_to_string(enhanced, config='--psm 6')
            pattern = self.config.get("code_pattern", r"[A-Z0-9]{6,15}")
            matches = re.findall(pattern, text.upper())
            if matches:
                return max(matches, key=len)
            return None
        except:
            return None
    
    def paste_code(self, code):
        try:
            selector = self.config.get("input_selector", "input[type='text']")
            elem = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            elem.clear()
            elem.send_keys(code)
            self.log(f"Pasted code: {code}")
            return True
        except Exception as e:
            self.log(f"Paste error: {e}")
            return False
    
    def press_enter(self):
        try:
            selector = self.config.get("input_selector", "input[type='text']")
            elem = self.driver.find_element(By.CSS_SELECTOR, selector)
            elem.send_keys(Keys.RETURN)
            return True
        except:
            try:
                active = self.driver.switch_to.active_element
                active.send_keys(Keys.RETURN)
                return True
            except:
                return False
    
    def spam_loop(self):
        interval = self.config.get("spam_interval", 2)
        self.log(f"Spam started (every {interval}s)")
        while self.is_running and self.is_spamming:
            if self.driver:
                self.press_enter()
            time.sleep(interval)
        self.log("Spam stopped")
    
    def reset_loop(self):
        reset_minutes = self.config.get("reset_interval", 15)
        reset_seconds = reset_minutes * 60
        self.log(f"Page will reset every {reset_minutes} minutes")
        while self.is_running:
            time.sleep(reset_seconds)
            if self.is_running and self.driver:
                self.log("Resetting page...")
                try:
                    self.driver.refresh()
                    time.sleep(2)
                    if self.current_code:
                        self.paste_code(self.current_code)
                except Exception as e:
                    self.log(f"Reset error: {e}")
    
    def scan_loop(self):
        interval = self.config.get("scan_interval", 2)
        self.log(f"Scanning every {interval}s")
        while self.is_running:
            try:
                if self.capture_region:
                    img = ImageGrab.grab(bbox=self.capture_region)
                else:
                    img = ImageGrab.grab()
                code = self.extract_code(img)
                if code and code != self.last_code:
                    self.last_code = code
                    self.current_code = code
                    self.log(f"NEW CODE FOUND: {code}")
                    if self.paste_code(code):
                        if not self.is_spamming:
                            self.start_spam()
            except:
                pass
            time.sleep(interval)
    
    def start_spam(self):
        if not self.is_spamming:
            self.is_spamming = True
            self.spam_thread = threading.Thread(target=self.spam_loop, daemon=True)
            self.spam_thread.start()
    
    def stop_spam(self):
        self.is_spamming = False
    
    def start(self):
        self.is_running = True
        if not self.start_browser():
            self.is_running = False
            return False
        self.scan_thread = threading.Thread(target=self.scan_loop, daemon=True)
        self.scan_thread.start()
        self.reset_thread = threading.Thread(target=self.reset_loop, daemon=True)
        self.reset_thread.start()
        self.log("Automation started!")
        return True
    
    def stop(self):
        self.is_running = False
        self.is_spamming = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        self.log("Automation stopped")
def run_gui():
    try:
        import tkinter as tk
    except ImportError:
        return False
    
    class App:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Telegram Code Scanner + Spam")
            self.root.geometry("520x780")
            self.root.configure(bg="#1a1a2e")
            self.scanner = None
            self.running = False
            self.region = None
            self.hotkey_active = False
            self.setup()
            self.setup_hotkey()
        
        def setup_hotkey(self):
            if keyboard:
                try:
                    keyboard.on_press_key("home", lambda _: self.root.after(0, self.select_region))
                    self.hotkey_active = True
                    self.log("HOME key hotkey enabled!")
                except:
                    self.log("Could not set HOME hotkey")
            else:
                self.log("Install 'keyboard' package for HOME hotkey")
        
        def setup(self):
            f = tk.Frame(self.root, bg="#1a1a2e", padx=20, pady=15)
            f.pack(fill="both", expand=True)
            
            tk.Label(f, text="TELEGRAM CODE SCANNER", font=("Consolas", 14, "bold"),
                    bg="#1a1a2e", fg="#00ffff").pack(pady=(0, 5))
            
            tk.Label(f, text="Press HOME key to select screen region", 
                    font=("Consolas", 9), bg="#1a1a2e", fg="#ff9900").pack(pady=(0, 10))
            
            tk.Label(f, text="Target URL:", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.url = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white",
                               font=("Consolas", 10))
            self.url.pack(fill="x", pady=(0, 8))
            self.url.insert(0, "https://www.jojobet1118.com/active-bonuses")
            
            tk.Label(f, text="Input Selector:", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.selector = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white",
                                    font=("Consolas", 10))
            self.selector.pack(fill="x", pady=(0, 8))
            self.selector.insert(0, "input[type='text']")
            
            tk.Label(f, text="Code Pattern (regex):", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.pattern = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white",
                                   font=("Consolas", 10))
            self.pattern.pack(fill="x", pady=(0, 8))
            self.pattern.insert(0, r"[A-Z0-9]{6,15}")
            
            intervals = tk.Frame(f, bg="#1a1a2e")
            intervals.pack(fill="x", pady=(0, 8))
            
            left = tk.Frame(intervals, bg="#1a1a2e")
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text="Scan Interval (sec):", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.scan_interval = tk.Entry(left, bg="#16213e", fg="white",
                                         insertbackground="white", font=("Consolas", 10), width=10)
            self.scan_interval.pack(anchor="w")
            self.scan_interval.insert(0, "2")
            
            right = tk.Frame(intervals, bg="#1a1a2e")
            right.pack(side="right", fill="x", expand=True)
            tk.Label(right, text="Spam Interval (sec):", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.spam_interval = tk.Entry(right, bg="#16213e", fg="white",
                                         insertbackground="white", font=("Consolas", 10), width=10)
            self.spam_interval.pack(anchor="w")
            self.spam_interval.insert(0, "1")
            
            tk.Label(f, text="Page Reset Interval (minutes):", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.reset_interval = tk.Entry(f, bg="#16213e", fg="white",
                                          insertbackground="white", font=("Consolas", 10))
            self.reset_interval.pack(fill="x", pady=(0, 8))
            self.reset_interval.insert(0, "15")
            
            tk.Label(f, text="Tesseract Path:", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.tess = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white",
                                font=("Consolas", 10))
            self.tess.pack(fill="x", pady=(0, 8))
            self.tess.insert(0, r"C:\Program Files\Tesseract-OCR\tesseract.exe")
            
            self.browser_var = tk.BooleanVar(value=True)
            tk.Checkbutton(f, text="Show Browser Window", variable=self.browser_var,
                          bg="#1a1a2e", fg="#00ffff", selectcolor="#16213e",
                          font=("Consolas", 10)).pack(anchor="w", pady=(0, 10))
            
            self.region_lbl = tk.Label(f, text="Screen Region: Not selected (press HOME)",
                                      bg="#1a1a2e", fg="#888888", font=("Consolas", 9))
            self.region_lbl.pack(anchor="w")
            
            tk.Button(f, text="SELECT SCREEN REGION (or press HOME)", command=self.select_region,
                     bg="#ff9900", fg="#1a1a2e", font=("Consolas", 10, "bold"),
                     cursor="hand2").pack(fill="x", pady=8)
            
            self.btn = tk.Button(f, text="START SCANNING + SPAM", command=self.toggle,
                                bg="#00ffff", fg="#1a1a2e", font=("Consolas", 12, "bold"),
                                cursor="hand2")
            self.btn.pack(fill="x", pady=8)
            
            self.status = tk.Label(f, text="Status: Idle", bg="#1a1a2e", fg="#888888",
                                  font=("Consolas", 10))
            self.status.pack(pady=5)
            
            tk.Label(f, text="Logs:", bg="#1a1a2e", fg="#00ffff",
                    font=("Consolas", 10)).pack(anchor="w")
            self.logs = tk.Text(f, bg="#16213e", fg="#00ff00", height=10,
                               font=("Consolas", 9))
            self.logs.pack(fill="both", expand=True)
            
            tk.Label(f, text="HOME = Select Region | Scans image for codes | Auto-spam Enter",
                    bg="#1a1a2e", fg="#666666", font=("Consolas", 8)).pack(pady=5)
        
        def log(self, msg):
            self.logs.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            self.logs.see("end")
        
        def select_region(self):
            self.log("Click and drag to select the code area...")
            self.root.iconify()
            time.sleep(0.3)
            
            self.overlay = tk.Toplevel()
            self.overlay.attributes('-fullscreen', True)
            self.overlay.attributes('-alpha', 0.3)
            self.overlay.configure(bg='gray')
            self.start_pos = None
            
            self.canvas = tk.Canvas(self.overlay, highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            self.rect = None
            
            self.overlay.bind('<Button-1>', self.on_press)
            self.overlay.bind('<B1-Motion>', self.on_drag)
            self.overlay.bind('<ButtonRelease-1>', self.on_release)
            self.overlay.bind('<Escape>', lambda e: self.cancel_selection())
        
        def cancel_selection(self):
            self.overlay.destroy()
            self.root.deiconify()
            self.log("Selection cancelled")
        
        def on_press(self, e):
            self.start_pos = (e.x_root, e.y_root)
        
        def on_drag(self, e):
            if self.start_pos:
                if self.rect:
                    self.canvas.delete(self.rect)
                self.rect = self.canvas.create_rectangle(
                    self.start_pos[0], self.start_pos[1], e.x_root, e.y_root,
                    outline='red', width=3)
        
        def on_release(self, e):
            if self.start_pos:
                x1, y1 = self.start_pos
                x2, y2 = e.x_root, e.y_root
                self.region = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
                self.region_lbl.config(text=f"Region: {self.region}", fg="#00ff00")
                self.log(f"Region selected: {self.region}")
                
                if self.scanner:
                    self.scanner.capture_region = self.region
            
            self.overlay.destroy()
            self.root.deiconify()
        
        def toggle(self):
            if not self.running:
                self.start()
            else:
                self.stop()
        
        def start(self):
            config = {
                "target_url": self.url.get(),
                "input_selector": self.selector.get(),
                "code_pattern": self.pattern.get(),
                "scan_interval": float(self.scan_interval.get()),
                "spam_interval": float(self.spam_interval.get()),
                "reset_interval": float(self.reset_interval.get()),
                "tesseract_path": self.tess.get(),
                "show_browser": self.browser_var.get(),
            }
            
            self.scanner = TelegramCodeScanner(config)
            self.scanner.log = self.log
            
            if self.region:
                self.scanner.capture_region = self.region
            
            if self.scanner.start():
                self.running = True
                self.btn.config(text="STOP", bg="#ff4444")
                self.status.config(text="Status: Scanning + Spamming...", fg="#00ff00")
            else:
                self.log("Failed to start!")
        
        def stop(self):
            self.running = False
            if self.scanner:
                self.scanner.stop()
            self.btn.config(text="START SCANNING + SPAM", bg="#00ffff")
            self.status.config(text="Status: Stopped", fg="#888888")
        
        def run(self):
            self.root.mainloop()
    
    App().run()
    return True
if __name__ == "__main__":
    run_gui()
