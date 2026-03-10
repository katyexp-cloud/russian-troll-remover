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
        self.root.geometry("400x400")
        self.root.attributes("-topmost", True)

        self.config_file = "config.json"
        self.cache_file = "cache.json"
        self.max_cache_size = 100
        
        self.config = self.load_config()

        self.target_label = tk.StringVar(value=self.config.get("target_label", "konstruktivní argument"))
        self.threshold = tk.DoubleVar(value=self.config.get("threshold", 0.7))
        self.other_labels = tk.StringVar(value=self.config.get("other_labels", "náhodný text, nadávka, urážka"))
        self.selected_model = tk.StringVar(value=self.config.get("model_name", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"))
        
        self.secondary_cache = self.load_cache()

        self.settings_win = None

        self.blacklist = self.load_blacklist()
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        self.btn_run = tk.Button(btn_frame, text="►", command=self.start_thread, 
                                 bg="green", fg="white", font=("Arial", 10, "bold"), width=10)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(btn_frame, text="⏹", command=self.stop_workflow, 
                                  bg="gray", fg="white", font=("Arial", 10, "bold"), width=10, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        self.btn_settings = tk.Button(btn_frame, text="Nastavení", command=self.open_settings, 
                                      bg="#679bf0", fg="white", font=("Arial", 10), width=10)
        self.btn_settings.pack(side=tk.LEFT, padx=5)

        self.log_frame = tk.Frame(root)
        self.log_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.log_area = tk.Text(self.log_frame, state='disabled', height=15, bg="black", fg="lightgreen")
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_area.yview)
        self.log_area.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack_forget()

        self.log_area.bind("<Enter>", lambda e: self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y))
        self.log_area.bind("<Leave>", lambda e: self.check_scrollbar_visibility())
        self.scrollbar.bind("<Enter>", lambda e: self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y))
        self.scrollbar.bind("<Leave>", lambda e: self.check_scrollbar_visibility())

        def check_scrollbar_visibility(self):
            if not (self.log_area.winfo_containing(*self.root.winfo_pointerxy()) == self.log_area or 
                    self.log_area.winfo_containing(*self.root.winfo_pointerxy()) == self.scrollbar):
                self.scrollbar.pack_forget()

        self.classifier = None
        self.is_running = False

    def load_blacklist(self):
        blacklist_path = "blacklist.json"
        if not os.path.exists(blacklist_path):
            default_blacklist = ["vyjebana pica"]
            with open(blacklist_path, "w", encoding="utf-8") as f:
                json.dump(default_blacklist, f, indent=4)
            return default_blacklist
        
        with open(blacklist_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def bring_to_front(self):
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()
        self.root.after(500, lambda: self.root.attributes("-topmost", False))

    def check_scrollbar_visibility(self):
        widget = self.root.winfo_containing(*self.root.winfo_pointerxy())
        if widget != self.log_area and widget != self.scrollbar:
            self.scrollbar.pack_forget()

    def load_config(self):
        default_config = {
            "model_name": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
            "target_label": "konstruktivní argument",
            "threshold": 0.7,
            "other_labels": "náhodný text, nadávka, urážka",
            "offsets": {"analyze_x": -20, "analyze_y": 0, "drag_start_x": 20, "drag_start_y": -25, "drag_end_x": -400, "drag_end_y": 0},
            "waits": {"scan_fail": 2.0, "copy_delay": 0.3, "action_shift": 1.0, "human_move_short": [0.2, 0.4], "human_move_med": [0.3, 0.5], 
                      "human_move_drag": [0.4, 0.6], "human_move_click": [0.25, 0.45], "post_click": [0.6, 0.9], "target2_interval": [0.4, 0.7], "between_targets": [0.5, 0.8]}
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: 
                    loaded = json.load(f)
                    default_config.update(loaded)
                    return default_config
            except json.JSONDecodeError:
                self.write_log("Chyba: config.json je poškozen. Používám výchozí.")
        
        # Save only if it doesn't exist
        with open(self.config_file, "w") as f: 
            json.dump(default_config, f, indent=4)
        return default_config

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f: 
                data = json.load(f)
                return data[-self.max_cache_size:]
        return []

    def save_to_cache(self, text):
        cleaned = self.clean_text(text)
        if cleaned and cleaned not in self.secondary_cache:
            if len(self.secondary_cache) >= self.max_cache_size:
                self.secondary_cache.pop(0)
            
            self.secondary_cache.append(cleaned)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.secondary_cache, f, indent=4)

    def clean_text(self, text):
        if "\r\n" in text:
            text = text.split("\r\n", 1)[1]
        
        nfkd_form = unicodedata.normalize('NFKD', text)
        text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        
        return text.encode('ascii', 'ignore').decode('ascii').lower().strip()

    def execute_target_sequence(self, x, y):
        waits = self.config["waits"]
        self.human_move(x, y, self.r_time(*waits["human_move_short"]))
        pyautogui.click()
        time.sleep(self.r_time(*waits["post_click"]))
        
        if self.find_and_tap('target2.png', 'Target 2 (1/2)'):
            time.sleep(self.r_time(*waits["target2_interval"]))
            if self.find_and_tap('target2.png', 'Target 2 (2/2)'):
                return False 
        return True

    def save_settings(self, win):
        self.config["model_name"] = self.selected_model.get()
        self.config["target_label"] = self.target_label.get()
        self.config["threshold"] = self.threshold.get()
        self.config["other_labels"] = self.other_labels.get()
        
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)
            
        self.write_log("Nastavení uloženo.")
        if self.classifier:
            self.classifier = None 
            self.write_log("Model bude při příštím spuštění znovu načten.")

        self.settings_win = None
        win.destroy()

    def open_settings(self):
        if hasattr(self, 'settings_win') and self.settings_win and self.settings_win.winfo_exists():
            self.settings_win.lift()
            self.settings_win.focus_force()
            return

        self.settings_win = tk.Toplevel(self.root)
        self.settings_win.title("Nastavení AI")
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        
        self.settings_win.geometry(f"380x310+{x + 10}+{y + 10}")
        self.settings_win.attributes("-topmost", True)
        
        tk.Label(self.settings_win, text="AI model:", font=("Arial", 9, "bold")).pack(pady=(10, 0))
        
        models = [
            "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
            "cross-encoder/nli-distilroberta-base",
            "valhalla/distilbart-mnli-12-1"
        ]
        ttk.Combobox(self.settings_win, textvariable=self.selected_model, values=models, width=45, state="readonly").pack(pady=5)

        tk.Label(self.settings_win, text="Na co se AI zaměřuje:", font=("Arial", 9, "bold")).pack(pady=5)
        tk.Entry(self.settings_win, textvariable=self.target_label, width=40).pack(pady=2)
        
        tk.Label(self.settings_win, text="Citlivostní práh (threshold):", font=("Arial", 9, "bold")).pack(pady=5)
        tk.Scale(self.settings_win, from_=0.1, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, variable=self.threshold).pack(fill=tk.X, padx=20)
        
        tk.Label(self.settings_win, text="Negativní štítky (oddělené čárkou)", font=("Arial", 9, "bold")).pack(pady=5)
        tk.Entry(self.settings_win, textvariable=self.other_labels, width=40).pack(pady=2)

        tk.Button(self.settings_win, text="Uložit a zavřít", command=lambda: self.save_settings(self.settings_win), bg="#679bf0", fg="white",
                  font=("Arial", 10), height=2).pack(pady=10, fill=tk.X, padx=10)
    
    def write_log(self, text):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log_area.see(tk.END); self.log_area.configure(state='disabled')

    def start_thread(self):
        if not self.is_running:
            self.config = self.load_config()
            self.is_running = True
            self.btn_run.config(state=tk.DISABLED, text="...")
            self.btn_stop.config(state=tk.NORMAL, bg="red") 
            threading.Thread(target=self.main_logic, daemon=True).start()

    def stop_workflow(self):
        self.is_running = False
        self.btn_stop.config(state=tk.DISABLED, bg="gray") # Reset to gray
        self.btn_run.config(state=tk.NORMAL, text="►")

    def r_time(self, min_t, max_t): return random.uniform(min_t, max_t)

    def human_move(self, dest_x, dest_y, duration):
        start_x, start_y = pyautogui.position()
        steps = random.randint(3, 5)
        for i in range(1, steps):
            ix = int(start_x + (dest_x - start_x) * (i / steps)) + random.randint(-20, 20)
            iy = int(start_y + (dest_y - start_y) * (i / steps)) + random.randint(-20, 20)
            pyautogui.moveTo(ix, iy, duration=duration/steps, tween=pyautogui.easeOutQuad)
        pyautogui.moveTo(dest_x + random.randint(-3, 3), dest_y + random.randint(-3, 3), duration=duration/steps)

    def find_and_tap(self, image, desc, conf=0.7):
        try:
            loc = pyautogui.locateCenterOnScreen(image, confidence=conf)
            if loc:
                self.write_log(f"Nalezeno: {desc}")
                self.human_move(loc.x, loc.y, self.r_time(*self.config["waits"]["human_move_click"]))
                pyautogui.click(); return True
            return False
        except: return False

    def is_constructive(self, text):
        if not text.strip() or self.classifier is None: return False
        target = self.target_label.get()
        labels = [target] + [s.strip() for s in self.other_labels.get().split(",")]
        result = self.classifier(text, candidate_labels=labels)
        score = dict(zip(result['labels'], result['scores']))[target]
        self.write_log(f"Skóre argumentu: {score:.2%}")
        return score >= self.threshold.get()

    def main_logic(self):
        try:
            if self.classifier is None:
                model_name = self.config["model_name"]
                self.write_log(f"Načítání AI: {model_name}")
                from transformers import pipeline

                #self.classifier = pipeline("zero-shot-classification", model="cross-encoder/nli-distilroberta-base")
                #self.classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")
                #self.classifier = pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
                self.classifier = pipeline("zero-shot-classification", model=model_name)

                self.write_log(f"AI načtena: {model_name}")

            while self.is_running:
                self.write_log("Skenuji potenciální cíle...")
                targets = list(pyautogui.locateAllOnScreen('target.png', confidence=0.7))
                if not targets:
                    self.write_log("Žádné cíle nebyly nalezeny.")
                    time.sleep(self.config["waits"]["scan_fail"])
                    continue

                targets.sort(key=lambda t: t.top)
                
                for t in targets:
                    if not self.is_running: break
                    cx, cy = pyautogui.center(t)
                    ox, oy = cx + self.config["offsets"]["analyze_x"], cy + self.config["offsets"]["analyze_y"]
                    
                    self.human_move(ox + self.config["offsets"]["drag_start_x"],
                                    oy + self.config["offsets"]["drag_start_y"], self.r_time(*self.config["waits"]["human_move_med"]))
                    pyautogui.mouseDown()
                    self.human_move(ox + self.config["offsets"]["drag_end_x"],
                                    oy + self.config["offsets"]["drag_end_y"], self.r_time(*self.config["waits"]["human_move_drag"]))
                    pyautogui.mouseUp()
                    
                    time.sleep(self.config["waits"]["copy_delay"])
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.2)
                    
                    raw_text = pyperclip.paste()
                    clean_msg = self.clean_text(raw_text)
                    
                    fast_cache = self.load_blacklist()
                    
                    action = False
                    if any(x in clean_msg for x in fast_cache):
                        self.write_log("Shoda v blacklistu. Odstraňuji...")
                        action = True
                    elif clean_msg in self.secondary_cache:
                        self.write_log("Shoda v paměti cache. Odstraňuji...")
                        action = True
                    elif not self.is_constructive(clean_msg):
                        self.write_log("Nízká úroveň argumentu. Ukládám a odstraňuji...")
                        self.save_to_cache(raw_text)
                        action = True
                    
                    if action:
                        finished_fully = not self.execute_target_sequence(cx, cy)
                        
                        if finished_fully:
                            self.write_log("Sekvence dokončena. Pokračuji v běhu.")
                        
                        time.sleep(self.config["waits"]["action_shift"])
                        continue 
                    
                    self.write_log("Selekce OK. Pokračuji dále.")
                    time.sleep(self.r_time(*self.config["waits"]["between_targets"]))

        except Exception as e: self.write_log(f"Chyba: {str(e)}")
        finally: self.stop_workflow()

if __name__ == "__main__":
    root = tk.Tk(); app = AIApp(root); root.mainloop()
