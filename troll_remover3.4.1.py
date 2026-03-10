import pyautogui
import pyperclip
import time
import os
import threading
import random
import json
import unicodedata
import tkinter as tk
from tkinter import scrolledtext, ttk

os.environ['HF_HUB_OFFLINE'] = '0'

class AIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nick Crompton 3.0")
        self.root.geometry("400x450")
        self.root.attributes("-topmost", True)

        # Essential Files
        self.config_file = "config.json"
        self.cache_file = "cache.json"
        self.max_cache_size = 100
        
        self.config = self.load_config()
        self.secondary_cache = self.load_cache()
        self.blacklist = self.load_blacklist()

        # GUI Variables
        self.target_label = tk.StringVar(value=self.config.get("target_label", "konstruktivní argument"))
        self.threshold = tk.DoubleVar(value=self.config.get("threshold", 0.3))
        self.other_labels = tk.StringVar(value=self.config.get("other_labels", "náhodný text, nadávka, urážka"))
        self.selected_model = tk.StringVar(value=self.config.get("model_name", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"))

        # UI Elements
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        self.btn_run = tk.Button(btn_frame, text="►", command=self.start_thread, bg="green", fg="white", width=10)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(btn_frame, text="⏹", command=self.stop_workflow, bg="gray", fg="white", width=10, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=15, bg="black", fg="lightgreen")
        self.log_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.classifier = None
        self.is_running = False

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f: return json.load(f)
        return {"model_name": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli", "target_label": "konstruktivní argument", "threshold": 0.3}

    def load_blacklist(self):
        if os.path.exists("blacklist.json"):
            with open("blacklist.json", "r", encoding="utf-8") as f: return json.load(f)
        return ["vyjebana pica"]

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f: return json.load(f)
        return []

    def save_to_cache(self, text):
        cleaned = self.clean_text(text)
        if cleaned and cleaned not in self.secondary_cache:
            self.secondary_cache.append(cleaned)
            with open(self.cache_file, "w", encoding="utf-8") as f: json.dump(self.secondary_cache[-100:], f, indent=4)

    def clean_text(self, text):
        if "\r\n" in text: text = text.split("\r\n", 1)[1]
        nfkd = unicodedata.normalize('NFKD', text)
        return "".join([c for c in nfkd if not unicodedata.combining(c)]).encode('ascii', 'ignore').decode('ascii').lower().strip()

    def write_log(self, text):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log_area.see(tk.END); self.log_area.configure(state='disabled')

    def r_time(self, min_t=0.3, max_t=0.6): return random.uniform(min_t, max_t)

    def human_move(self, dest_x, dest_y, total_duration):
        start_x, start_y = pyautogui.position()
        steps = random.randint(4, 6)
        for i in range(1, steps):
            wobble = random.randint(-2, 2)
            ix = int(start_x + (dest_x - start_x) * (i / steps)) + wobble
            iy = int(start_y + (dest_y - start_y) * (i / steps)) + wobble
            pyautogui.moveTo(ix, iy, duration=total_duration/steps, tween=pyautogui.easeOutQuad)
        pyautogui.moveTo(dest_x, dest_y, duration=0.05)

    def find_and_tap(self, image, desc):
        try:
            loc = pyautogui.locateCenterOnScreen(image, confidence=0.7)
            if loc:
                self.write_log(f"Nalezeno: {desc}")
                self.human_move(loc.x, loc.y, self.r_time(0.3, 0.5))
                pyautogui.click(); return True
            return False
        except: return False

    def execute_target_sequence(self, x, y):
        # Click the initial target point (the original source)
        self.human_move(x, y, self.r_time(0.3, 0.5))
        pyautogui.click()
        time.sleep(self.r_time(0.6, 0.8)) # Hard wait for UI
        
        # Handle the two-stage Target2 process
        if self.find_and_tap('target2.png', 'Target 2 (1/2)'):
            time.sleep(self.r_time(0.5, 0.7))
            self.find_and_tap('target2.png', 'Target 2 (2/2)')

    def is_constructive(self, text):
        if not text.strip() or self.classifier is None: return False
        labels = [self.target_label.get()] + [s.strip() for s in self.other_labels.get().split(",")]
        result = self.classifier(text, candidate_labels=labels)
        score = dict(zip(result['labels'], result['scores']))[self.target_label.get()]
        self.write_log(f"Skóre: {score:.2%}")
        return score >= self.threshold.get()

    def start_thread(self):
        if not self.is_running:
            self.is_running = True
            self.btn_run.config(state=tk.DISABLED, text="...")
            self.btn_stop.config(state=tk.NORMAL, bg="red")
            threading.Thread(target=self.main_logic, daemon=True).start()

    def stop_workflow(self):
        self.is_running = False
        self.btn_stop.config(state=tk.DISABLED, bg="gray")
        self.btn_run.config(state=tk.NORMAL, text="►")

    def main_logic(self):
        try:
            if self.classifier is None:
                self.write_log("Načítání AI...")
                from transformers import pipeline
                self.classifier = pipeline("zero-shot-classification", model=self.selected_model.get())
                self.write_log("AI připravena.")

            while self.is_running:
                self.write_log("🔍 Locating targets...")
                targets = list(pyautogui.locateAllOnScreen('target.png', confidence=0.7))
                
                if not targets:
                    self.write_log("📜 Scrolling...")
                    pyautogui.scroll(-500)
                    time.sleep(1.5)
                    continue

                targets.sort(key=lambda t: t.top)

                for t in targets:
                    if not self.is_running: break
                    
                    cx, cy = pyautogui.center(t)
                    # EXACT OFFSET LOGIC
                    off_x, off_y = cx - 20, cy + 20
                    
                    self.write_log(f"📍 Targeting: ({off_x}, {off_y})")
                    self.human_move(off_x, off_y, self.r_time(0.4, 0.6))
                    
                    # Highlight Text Sequence
                    self.human_move(off_x + 20, off_y - 5, self.r_time(0.3, 0.4))
                    pyautogui.mouseDown()
                    self.human_move(off_x - 400, off_y, self.r_time(0.4, 0.6))
                    pyautogui.mouseUp()
                    
                    time.sleep(0.4)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.2)
                    
                    raw_text = pyperclip.paste()
                    clean_msg = self.clean_text(raw_text)
                    
                    action = False
                    if any(x in clean_msg for x in self.blacklist):
                        self.write_log("Blacklist match!")
                        action = True
                    elif clean_msg in self.secondary_cache:
                        self.write_log("Cache match!")
                        action = True
                    elif not self.is_constructive(clean_msg):
                        self.write_log("AI Flagged!")
                        self.save_to_cache(raw_text)
                        action = True
                    
                    if action:
                        self.execute_target_sequence(cx, cy)
                        time.sleep(1.0)
                    else:
                        self.write_log("OK.")
                        time.sleep(self.r_time(0.5, 0.8))

                # Post-screen scroll
                self.write_log("Screen done. Scrolling...")
                last_cx, last_cy = pyautogui.center(targets[-1])
                self.human_move(last_cx, last_cy, 0.3)
                pyautogui.scroll(-500)
                time.sleep(1.2)

        except Exception as e:
            self.write_log(f"❌ Error: {str(e)}")
            pyautogui.mouseUp()
        finally:
            self.stop_workflow()

if __name__ == "__main__":
    root = tk.Tk(); app = AIApp(root); root.mainloop()
