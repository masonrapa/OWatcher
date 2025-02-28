from selenium.webdriver.firefox.options import Options
from tkinter import Text, ttk, Canvas
from PIL import Image, ImageTk
from selenium import webdriver
import tkinter as tk
import numpy as np
import webbrowser
import builtwith
import argparse
import pickle
import json
import time
import os
import re

parser = argparse.ArgumentParser(description="Script con argumentos --ip, --port y --auto.")

parser.add_argument("--ip", type=str, default="127.0.0.1", help="Dirección IP (por defecto: 127.0.0.1)")
parser.add_argument("--port", type=int, default=9050, help="Puerto (por defecto: 9050)")
parser.add_argument("--auto", action="store_true", help="Modo automático (por defecto: False)")
args = parser.parse_args()

with open("model.ai", "rb") as f:
    product_classifier = pickle.load(f)

options = Options()
options.headless = True
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--allow-root")

options.set_preference("network.proxy.type", 1)
options.set_preference("network.proxy.socks", args.ip)
options.set_preference("network.proxy.socks_port", args.port)
options.set_preference("network.proxy.socks_remote_dns", True)

visualizado = Options()
visualizado.set_preference("network.proxy.type", 1)
visualizado.set_preference("network.proxy.socks", args.ip)
visualizado.set_preference("network.proxy.socks_port", args.port)
visualizado.set_preference("network.proxy.socks_remote_dns", True)

screenshot_dir = os.path.join(os.getcwd(), "data")
os.makedirs(screenshot_dir, exist_ok=True)

IMAGE_FOLDER = "./data"
TEXT_FILE = "onions.src"
ICON_ONION = "onion.png"

def get_site_title(driver):
    try:
        return driver.title if driver.title else "Sin título"
    except:
        return "Error obteniendo título"

def classify_products(html):
    try:
        words = re.findall(r"\b[a-zA-Z]+\b", html.lower())
        phrases = [' '.join(words[i:i+3]) for i in range(len(words) - 2)]
        categories = set()
        for phrase in phrases:
            probs = product_classifier.predict_proba([phrase])[0]
            predicted_category = product_classifier.classes_[np.argmax(probs)]
            confidence = np.max(probs)
            if confidence >= 0.3:
                categories.add(predicted_category)
        return list(categories) if categories else ["Unknown"]
    except Exception as e:
        print(f"Error clasificando productos: {e}")
        return ["Error"]

def detect_technology(driver):
    try:
        html = driver.page_source.lower()
        try:
            url = driver.current_url
            tech_data = builtwith.builtwith(url)
            if tech_data:
                detected_techs = [tech.capitalize() for tech in tech_data.keys()]
                if detected_techs:
                    return detected_techs
        except Exception:
            product_classifier

        tech_map = {
            "WordPress": ["wp-content", "wp-includes", "wordpress"],
            "Shopify": ["cdn.shopify", "shopify"],
            "Magento": ["mage-", "magento"],
            "Joomla": ["joomla", "joomla.org"],
            "Drupal": ["drupal", "drupal.org"],
            "PHP": [".php", "php/"],
            "React": ["react.", "data-reactid"],
            "Angular": ["ng-app", "angular"],
            "Vue.js": ["vuejs", "vue."],
            "Django": ["django", "csrfmiddlewaretoken"],
            "Flask": ["flask", "werkzeug"],
            "Ruby on Rails": ["rails", "ruby-on-rails"],
            "ASP.NET": ["asp.net", "aspnet"],
            "Laravel": ["laravel", "x-powered-by: laravel"],
            "Spring Boot": ["spring", "spring-boot"],
            "Node.js": ["node.js", "express"],
            "Bootstrap": ["bootstrap", "bootstrapcdn"],
            "Tailwind": ["tailwindcss", "tailwind"],
            "jQuery": ["jquery", "jquery.com"],
            "Cloudflare": ["cloudflare", "__cfduid"]
        }

        detected = set()
        for tech, patterns in tech_map.items():
            for pattern in patterns:
                if re.search(rf"\b{re.escape(pattern)}\b", html):
                    detected.add(tech)
        return list(detected) if detected else []

    except Exception:
        return []

def load_onion_sites():
    with open("onions.src", "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("OWatcher")
        self.root.geometry("850x600")
        self.root.bind_all("<MouseWheel>", self.disable_scroll)
        self.main_screen()
    
    def main_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.bind_all("<MouseWheel>", self.enable_scroll)
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        btn_font = ("Arial", 16, "bold")
        self.icon_onion = ImageTk.PhotoImage(Image.open(ICON_ONION).resize((50, 50)))
        scan_btn = tk.Button(top_frame, text="INICIAR ESCANEO", command=lambda: self.scan_action(load_onion_sites()), height=2, font=btn_font)
        scan_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        file_btn = tk.Button(top_frame, image=self.icon_onion, command=lambda: self.open_text_editor(TEXT_FILE), height=60, width=1)
        file_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(0, 5))
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        canvas = Canvas(container)
        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame.bind("<Configure>", update_scroll_region)
        def on_mouse_wheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.root.bind("<MouseWheel>", on_mouse_wheel)
        self.root.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        self.root.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        self.root.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(-1 * (e.delta // 120), "units"))
        canvas.pack(fill=tk.BOTH, expand=True)
        self.load_images(frame)

    def scan_action(self, array):
        driver = webdriver.Firefox(options=options)
        for site in array:
            if not site.startswith("http"): 
                site = "http://" + site
            try:
                driver.set_page_load_timeout(30)
                driver.get(site + ".onion")
                time.sleep(5)
                title = get_site_title(driver)
                tech = detect_technology(driver)
                html = driver.page_source
                products_found = classify_products(html)
                is_counterfeit = "counterfeit" in html.lower()
                screenshot_path = os.path.join(screenshot_dir, f"{title[:24]}.png")
                json_path = os.path.join(screenshot_dir, f"{title[:24]}.json")
                driver.save_screenshot(screenshot_path)
                site_data = {
                    "titulo": title,
                    "direccion": site,
                    "tecnologia": tech,
                    "productos": products_found,
                    "counterfeit": is_counterfeit
                }
                with open(json_path, "w") as json_file:
                    json.dump(site_data, json_file, indent=4)
            except Exception as e:
                print(f"Error al acceder a {site}: {e}")

        driver.quit()
        self.main_screen()
    
    def load_images(self, parent):
        images = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(".png")]
        cols = 4
        for i, img_name in enumerate(images):
            img_path = os.path.join(IMAGE_FOLDER, img_name)
            json_path = img_path.replace(".png", ".json")
            img = Image.open(img_path).resize((200, 150))
            photo = ImageTk.PhotoImage(img)
            btn = tk.Button(parent, image=photo, command=lambda p=img_path, j=json_path: self.show(p, j), borderwidth=0, highlightthickness=0)
            btn.image = photo
            btn.grid(row=i // cols * 2, column=i % cols, padx=5, pady=10)
            label = tk.Label(parent, text=img_name[:-4], font=("Arial", 12, "bold"))
            label.grid(row=(i // cols * 2) + 1, column=i % cols)
    
    def delete_files(self, path, json_path):
        try:
            if os.path.exists(path):
                os.remove(path)
            if os.path.exists(json_path):
                os.remove(json_path)
            self.main_screen()
        except Exception as e:
            print(f"Error eliminando archivos: {e}")

    def show(self, path, json_path):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.bind_all("<MouseWheel>", self.disable_scroll)
        
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"titulo": "Sin datos", "direccion": "N/A", "tecnologia": "N/A", "productos": [], "counterfeit": False}
        
        def open_url():
            driver = webdriver.Firefox(options=visualizado)
            driver.get(data['direccion']+".onion")
        
        title_label = tk.Label(self.root, text=f"{data['titulo']}", font=("Arial", 14, "bold"), fg="blue", cursor="hand2")
        title_label.pack()
        title_label.bind("<Button-1>", lambda e: open_url())
        
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        img = Image.open(path).resize((600, 450))
        photo = ImageTk.PhotoImage(img)
        img_label = tk.Label(content_frame, image=photo)
        img_label.image = photo
        img_label.grid(row=0, column=0, rowspan=3, padx=10)
        
        details_frame = tk.Frame(content_frame)
        details_frame.grid(row=0, column=1, sticky="nw")
                
        tk.Label(details_frame, text="Tecnología:", font=("Arial", 12, "bold")).pack(anchor="w")
        for producto in data["tecnologia"]:
            tk.Label(details_frame, text=f"- {producto}", font=("Arial", 12)).pack(anchor="w")
        tk.Label(details_frame, text="").pack(anchor="w")
        tk.Label(details_frame, text="Productos:", font=("Arial", 12, "bold")).pack(anchor="w")
        for producto in data["productos"]:
            tk.Label(details_frame, text=f"- {producto}", font=("Arial", 12)).pack(anchor="w")
        tk.Label(details_frame, text="").pack(anchor="w")
        counterfeit_text = "Sí" if data["counterfeit"] else "No"
        tk.Label(details_frame, text=f"Counterfeit: {counterfeit_text}", font=("Arial", 12, "bold"), fg="green" if data["counterfeit"] else "red").pack(anchor="w")
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        tk.Button(button_frame, text="ACTUALIZAR", command=lambda: self.scan_action([data['direccion']]), height=2, font=("Arial", 16, "bold"), bg="green", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(button_frame, text="VOLVER", command=self.main_screen, height=2, font=("Arial", 16, "bold"), bg="blue", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(button_frame, text="ELIMINAR", command=lambda: self.delete_files(path, json_path), height=2, font=("Arial", 16, "bold"), bg="red", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X)

    def open_text_editor(self, file_path):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.bind_all("<MouseWheel>", self.disable_scroll)
        text_area = Text(self.root, wrap=tk.WORD, font=("Arial", 14))
        text_area.pack(expand=True, fill=tk.BOTH)
        try:
            with open(file_path, "r") as f:
                text_area.insert(tk.END, f.read())
        except FileNotFoundError:
            pass
        save_btn = tk.Button(self.root, text="Guardar", command=lambda: self.save_and_return(file_path, text_area), height=2, font=("Arial", 16, "bold"))
        save_btn.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
    
    def save_and_return(self, file_path, text_area):
        with open(file_path, "w") as f:
            f.write(text_area.get("1.0", tk.END))
        self.main_screen()
    
    def enable_scroll(self, event=None):
        self.root.bind_all("<MouseWheel>", lambda event: self.root.event_generate("<Configure>"))
    
    def disable_scroll(self, event=None):
        self.root.unbind_all("<MouseWheel>")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
