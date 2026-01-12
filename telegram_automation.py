#!/usr/bin/env python3
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
class TelegramCodeScanner:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.is_running = False
        self.last_code = ""
        self.capture_region = None
        
        if pytesseract and os.path.exists(config.get("tesseract_path", "")):
            pytesseract.pytesseract.tesseract_cmd = config["tesseract_path"]
    
    def log(self, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def start_browser(self):
        try:
            options = Options()
            if not self.config.get("show_browser", True):
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.get(self.config["target_url"])
            self.log(f"Opened: {self.config['target_url']}")
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
            matches = re.findall(self.config.get("code_pattern", r"[A-Z0-9]{6,15}"), text)
            return max(matches, key=len) if matches else None
        except:
            return None
    
    def paste_code(self, code):
        try:
            elem = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.config["input_selector"]))
            )
            elem.clear()
            elem.send_keys(code)
            if self.config.get("auto_submit", True):
                elem.send_keys(Keys.RETURN)
            self.log(f"Submitted: {code}")
            return True
        except Exception as e:
            self.log(f"Paste error: {e}")
            return False
    
    def scan(self):
        try:
            if self.capture_region:
                img = ImageGrab.grab(bbox=self.capture_region)
            else:
                img = ImageGrab.grab()
            code = self.extract_code(img)
            if code and code != self.last_code:
                self.last_code = code
                self.log(f"Found code: {code}")
                self.paste_code(code)
        except Exception as e:
            self.log(f"Scan error: {e}")
    
    def start(self):
        self.is_running = True
        return self.start_browser()
    
    def stop(self):
        self.is_running = False
        if self.driver:
            self.driver.quit()
def run_gui():
    import tkinter as tk
    
    class App:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Telegram Code Scanner")
            self.root.geometry("500x650")
            self.root.configure(bg="#1a1a2e")
            self.scanner = None
            self.running = False
            self.region = None
            self.setup()
        
        def setup(self):
            f = tk.Frame(self.root, bg="#1a1a2e", padx=20, pady=20)
            f.pack(fill="both", expand=True)
            
            tk.Label(f, text="TELEGRAM CODE SCANNER", font=("Consolas", 14, "bold"), 
                    bg="#1a1a2e", fg="#00ffff").pack(pady=10)
            
            tk.Label(f, text="Target URL:", bg="#1a1a2e", fg="#00ffff").pack(anchor="w")
            self.url = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white")
            self.url.pack(fill="x", pady=(0,10))
            self.url.insert(0, "https://www.jojobet1118.com/active-bonuses")
            
            tk.Label(f, text="Input Selector:", bg="#1a1a2e", fg="#00ffff").pack(anchor="w")
            self.selector = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white")
            self.selector.pack(fill="x", pady=(0,10))
            self.selector.insert(0, "input[type='text']")
            
            tk.Label(f, text="Code Pattern:", bg="#1a1a2e", fg="#00ffff").pack(anchor="w")
            self.pattern = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white")
            self.pattern.pack(fill="x", pady=(0,10))
            self.pattern.insert(0, r"[A-Z0-9]{6,15}")
            
            tk.Label(f, text="Scan Interval (sec):", bg="#1a1a2e", fg="#00ffff").pack(anchor="w")
            self.interval = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white")
            self.interval.pack(fill="x", pady=(0,10))
            self.interval.insert(0, "2")
            
            tk.Label(f, text="Tesseract Path:", bg="#1a1a2e", fg="#00ffff").pack(anchor="w")
            self.tess = tk.Entry(f, bg="#16213e", fg="white", insertbackground="white")
            self.tess.pack(fill="x", pady=(0,10))
            self.tess.insert(0, r"C:\Program Files\Tesseract-OCR\tesseract.exe")
            
            self.auto_var = tk.BooleanVar(value=True)
            tk.Checkbutton(f, text="Auto-submit", variable=self.auto_var,
                          bg="#1a1a2e", fg="#00ffff", selectcolor="#16213e").pack(anchor="w")
            
            self.browser_var = tk.BooleanVar(value=True)
            tk.Checkbutton(f, text="Show Browser", variable=self.browser_var,
                          bg="#1a1a2e", fg="#00ffff", selectcolor="#16213e").pack(anchor="w", pady=(0,10))
            
            self.region_lbl = tk.Label(f, text="No region selected", bg="#1a1a2e", fg="#888")
            self.region_lbl.pack()
            
            tk.Button(f, text="SELECT REGION", command=self.select_region,
                     bg="#ff9900", fg="black", font=("Consolas", 10, "bold")).pack(fill="x", pady=5)
            
            self.btn = tk.Button(f, text="START SCANNING", command=self.toggle,
                                bg="#00ffff", fg="black", font=("Consolas", 11, "bold"))
            self.btn.pack(fill="x", pady=5)
            
            self.status = tk.Label(f, text="Status: Idle", bg="#1a1a2e", fg="#888")
            self.status.pack(pady=5)
            
            tk.Label(f, text="Logs:", bg="#1a1a2e", fg="#00ffff").pack(anchor="w")
            self.logs = tk.Text(f, bg="#16213e", fg="#0f0", height=8, font=("Consolas", 9))
            self.logs.pack(fill="both", expand=True)
        
        def log(self, msg):
            self.logs.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            self.logs.see("end")
        
        def select_region(self):
            self.log("Click and drag to select region...")
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
        
        def on_press(self, e):
            self.start_pos = (e.x_root, e.y_root)
        
        def on_drag(self, e):
            if self.start_pos:
                if self.rect: self.canvas.delete(self.rect)
                self.rect = self.canvas.create_rectangle(
                    self.start_pos[0], self.start_pos[1], e.x_root, e.y_root,
                    outline='red', width=2)
        
        def on_release(self, e):
            if self.start_pos:
                x1, y1 = self.start_pos
                x2, y2 = e.x_root, e.y_root
                self.region = (min(x1,x2), min(y1,y2), max(x1,x2), max(y1,y2))
                self.region_lbl.config(text=f"Region: {self.region}", fg="#0f0")
                self.log(f"Region set: {self.region}")
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
                "tesseract_path": self.tess.get(),
                "auto_submit": self.auto_var.get(),
                "show_browser": self.browser_var.get(),
            }
            self.scanner = TelegramCodeScanner(config)
            self.scanner.log = self.log
            if self.region:
                self.scanner.capture_region = self.region
            
            if self.scanner.start():
                self.running = True
                self.btn.config(text="STOP", bg="#ff4444")
                self.status.config(text="Scanning...", fg="#0f0")
                self.scan_loop()
        
        def stop(self):
            self.running = False
            if self.scanner:
                self.scanner.stop()
            self.btn.config(text="START SCANNING", bg="#00ffff")
            self.status.config(text="Stopped", fg="#888")
        
        def scan_loop(self):
            if self.running and self.scanner:
                self.scanner.scan()
                self.root.after(int(float(self.interval.get()) * 1000), self.scan_loop)
        
        def run(self):
            self.root.mainloop()
    
    App().run()
if __name__ == "__main__":
    run_gui()
