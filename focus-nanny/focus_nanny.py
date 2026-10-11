#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focus — следит чем ты занимаешься и напоминает о лимитах.
check_interval: читает заголовок окна (0% CPU)
vision_interval: скриншот + vision LLM (тяжелое, но умное)
"""
import time, random, base64, io, yaml, sys, re, threading, os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except: pass
import psutil
import win32gui, win32process
import mss as mss_module
from PIL import Image
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"
os.environ["no_proxy"] = "localhost,127.0.0.1,::1"
try:
    import ollama
    HAS_OLLAMA = True
    try:
        OLLAMA_CLIENT = ollama.Client(host="http://127.0.0.1:11434", trust_env=False, timeout=120)
    except TypeError:
        OLLAMA_CLIENT = ollama.Client(host="http://127.0.0.1:11434", timeout=120)
except: 
    HAS_OLLAMA = False
    OLLAMA_CLIENT = None
try:
    import pyttsx3
    HAS_TTS = True
except: HAS_TTS = False
try:
    from plyer import notification
    HAS_PLYER = True
except: HAS_PLYER = False

CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd: return None, None, ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        title = win32gui.GetWindowText(hwnd) or ""
        try: exe = psutil.Process(pid).name()
        except: exe = ""
        return pid, exe, title
    except: return None, None, ""

class VisionWatcher:
    def __init__(self, cfg):
        self.cfg = cfg
        self.enabled = cfg.get("enable_vision", True)
        self.model = cfg.get("vision_model","moondream")
        self.last_result = "не проверено"
        self.last_time = 0
        self._ensure_model()

    def _ensure_model(self):
        if not HAS_OLLAMA or not self.enabled or OLLAMA_CLIENT is None: return
        try:
            resp = OLLAMA_CLIENT.list()
            raw = resp.get("models",[]) if isinstance(resp, dict) else getattr(resp, "models", [])
            models = [(m.get("name") or m.get("model")) if isinstance(m, dict) else getattr(m,"model", getattr(m,"name","")) for m in raw]
            has = any(self.model in m for m in models)
            if not has:
                print(f"[vision] качаю {self.model} (~1.7GB)... ollama pull {self.model}")
                OLLAMA_CLIENT.pull(self.model)
                print("[vision] готово!")
            else:
                print(f"[vision] модель {self.model} найдена ✓")
        except Exception as e:
            print(f"[vision] ошибка: {e}")
            print(f"[vision] -> vision временно отключён. Поставь в config.yaml enable_vision: false")
            print(f"[vision]    чтобы не спамить, и включи позже когда скачаешь: ollama pull {self.model}")
            self.enabled = False
            self.cfg["enable_vision"] = False

    def capture_b64(self, max_side=768) -> str:
        with mss_module.MSS() as sct:
            img = sct.grab(sct.monitors[1])
            pil = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            pil.thumbnail((max_side, max_side), Image.LANCZOS)
            buf = io.BytesIO()
            pil.save(buf, format="JPEG", quality=70)
            return base64.b64encode(buf.getvalue()).decode()

    def analyze(self) -> str:
        if not self.enabled or not HAS_OLLAMA or OLLAMA_CLIENT is None: return "vision disabled"
        try:
            b64 = self.capture_b64()
            prompt = "Describe the screenshot briefly."
            resp = OLLAMA_CLIENT.chat(model=self.model, messages=[{"role":"user","content":prompt,"images":[b64]}], options={"temperature":0.5,"num_predict":180,"repeat_penalty":1.1})
            try:
                text = resp["message"]["content"].strip() if isinstance(resp, dict) else resp.message.content.strip()
            except: text = str(resp)[:400]
            if not text:
                resp2 = OLLAMA_CLIENT.chat(model=self.model, messages=[{"role":"user","content":prompt,"images":[b64]}], options={"temperature":0.7,"num_predict":180,"repeat_penalty":1.1})
                try: text = resp2["message"]["content"].strip() if isinstance(resp2, dict) else resp2.message.content.strip()
                except: text = ""
            if not text: text = "A computer screen with code editor [WORK]"
            low=text.lower()
            if "[WORK]" not in text and "[GAME]" not in text and "[YOUTUBE" not in text and "[OTHER]" not in text:
                if any(k in low for k in ["code editor","programming","code","html","vs code","visual studio"]):
                    text += " [WORK]"
                elif any(k in low for k in ["game","steam","dota","cs","minecraft","valorant"]):
                    text += " [GAME]"
                elif "youtube" in low:
                    if any(k in low for k in ["tutorial","lesson","course","learn","python","guide"]):
                        text += " [YOUTUBE_EDU]"
                    else:
                        text += " [YOUTUBE_FUN]"
                else:
                    text += " [OTHER]"
            self.last_result = text; self.last_time = time.time()
            return text
        except Exception as e:
            print(f"[vision] error {e}"); return f"vision error: {e}"

    def parse_tag(self, text: str):
        m = re.search(r"\[(GAME|YOUTUBE_FUN|YOUTUBE_EDU|WORK|OTHER)\]", text)
        if m: return m.group(1).lower()
        t = text.lower()
        if "игр" in t: return "game"
        if "развлекат" in t and "ютуб" in t: return "youtube_fun"
        if "обуч" in t and "ютуб" in t: return "youtube_edu"
        if "программир" in t or "код" in t or "учит" in t: return "work"
        return "other"

class Nanny:
    def __init__(self, cfg):
        self.cfg = cfg; self.engine = None
        if cfg.get("enable_voice") and HAS_TTS:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 175)
                try: self.engine.setProperty("volume", float(cfg.get("voice_volume", 0.35)))
                except: pass
                for v in self.engine.getProperty("voices"):
                    if "russian" in v.name.lower() or "irina" in v.name.lower():
                        self.engine.setProperty("voice", v.id); break
            except Exception as e: print(f"[tts] {e}")

    def speak(self, text: str):
        print(f"\n⏰ Focus: {text}\n")
        if self.engine:
            try: self.engine.say(text); self.engine.runAndWait()
            except: pass
        if self.cfg.get("enable_notifications") and HAS_PLYER:
            try: notification.notify(title="Focus — Лимит!", message=text, timeout=5, app_name="Focus")
            except: pass

    def roast_llm(self, activity: str, minutes: int, vision_text: str, title: str):
        if not HAS_OLLAMA or OLLAMA_CLIENT is None: return None
        chat_model = self.cfg.get("chat_model","llama3.1:8b")
        try:
            prompt = (f"Ты — строгая но смешная няня. Пользователь {minutes} мин: {activity}. "
                      f"Окно: \"{title[:80]}\". Видит нейросеть: \"{vision_text[:120]}\". "
                      f"Коротко напомни на русском (1-2 предл.), что лимит превышен и пора вернуться к работе. Без матов.")
            resp = OLLAMA_CLIENT.chat(model=chat_model, messages=[{"role":"user","content":prompt}], options={"num_predict": 90})
            return resp["message"]["content"].strip()
        except: return None

    def get_phrase(self, activity: str, minutes: int, vision_text: str, title: str) -> str:
        llm = self.roast_llm(activity, minutes, vision_text, title)
        if llm: return llm
        phrases = self.cfg.get("phrases",[])
        hm = {"game":"играешь","youtube_fun":"смотришь развлекательный ютуб","youtube":"смотришь ютуб"}.get(activity, activity)
        if phrases: return random.choice(phrases).format(minutes=minutes, activity=hm)
        return f"Лимит! Ты уже {minutes} минут {hm} — пора сделать паузу и вернуться к фокусу."

def is_youtube_title(title: str) -> bool:
    return "youtube" in title.lower()

def classify(title: str, exe: str, cfg) -> str:
    exe_l = (exe or "").lower()
    title_l = (title or "").lower()
    games = [g.lower() for g in cfg.get("games",[])]
    if any(g == exe_l or g in exe_l for g in games):
        return "game"
    if any(k in title_l for k in ["dota","cs2","valorant","minecraft","gta","elden ring","cyberpunk"]):
        if exe_l not in ["chrome.exe","msedge.exe","firefox.exe",""] and exe_l.endswith(".exe"):
            return "game"
    if is_youtube_title(title):
        edu_keys = [k.lower() for k in cfg.get("youtube_edu_keywords",[])]
        fun_keys = [k.lower() for k in cfg.get("youtube_fun_keywords",[])]
        if any(k in title_l for k in edu_keys): return "youtube_edu"
        if any(k in title_l for k in fun_keys): return "youtube_fun"
        return "youtube"
    work_keys = [k.lower() for k in cfg.get("work_keywords",[])]
    if any(k in title_l or k in exe_l for k in work_keys): return "work"
    if not title.strip(): return "idle"
    return "other"

def main():
    cfg = load_config()
    print("="*60)
    print("Focus запущена")
    print(f"   check={cfg['check_interval']}s vision={cfg['vision_interval']}s")
    print(f"   vision={cfg['enable_vision']} ({cfg['vision_model']}) voice={cfg['enable_voice']}")
    print("   Ctrl+C чтобы остановить")
    print("="*60)
    vision = VisionWatcher(cfg)
    nanny = Nanny(cfg)
    limits = cfg.get("limits",{})
    game_limit = limits.get("game_minutes",30)*60
    yt_fun_limit = limits.get("youtube_entertainment_minutes",15)*60
    yt_total_limit = limits.get("youtube_total_minutes",30)*60
    nag_interval = limits.get("nag_interval_minutes",5)*60
    streak = defaultdict(float)
    current_cat = "other"; last_cat = None; last_nag = 0
    vision_text = "еще не смотрели"; vision_tag = "other"
    check_interval = cfg.get("check_interval",3)
    vision_interval = cfg.get("vision_interval",45)
    last_vision = 0; last_print = 0
    try:
        while True:
            pid, exe, title = get_active_window()
            cat = classify(title, exe, cfg)
            if cat == "youtube" and vision_tag in ["youtube_fun","youtube_edu"]:
                if time.time() - vision.last_time < vision_interval*2:
                    cat = vision_tag
            if cat == current_cat:
                streak[cat] += check_interval
            else:
                if last_cat != cat:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] -> {cat:15} | {exe:20} | {title[:60]}")
                current_cat = cat
                if cat == "work":
                    streak["game"]=0; streak["youtube_fun"]=0; streak["youtube"]=0
                last_cat = cat
            if cfg.get("enable_vision") and time.time() - last_vision > vision_interval:
                last_vision = time.time()
                def do_vision():
                    nonlocal vision_text, vision_tag
                    print("[vision] 📸 скриншот -> LLM...")
                    t = vision.analyze(); tag = vision.parse_tag(t)
                    vision_text=t; vision_tag=tag
                    print(f"[vision] {t} -> {tag}")
                threading.Thread(target=do_vision, daemon=True).start()
            now = time.time(); should_nag=False; reason=""; minutes=0
            if streak["game"] > game_limit:
                should_nag=True; minutes=int(streak["game"]//60); reason="game"
            elif streak["youtube_fun"] > yt_fun_limit:
                should_nag=True; minutes=int(streak["youtube_fun"]//60); reason="youtube_fun"
            elif streak["youtube"] > yt_total_limit:
                should_nag=True; minutes=int(streak["youtube"]//60); reason="youtube"
            elif streak["youtube_fun"]+streak["youtube"] > yt_total_limit:
                should_nag=True; minutes=int((streak["youtube_fun"]+streak["youtube"])//60); reason="youtube"
            if should_nag and (now - last_nag > nag_interval):
                last_nag=now
                phrase = nanny.get_phrase(reason, minutes, vision_text, title)
                nanny.speak(phrase)
            if time.time() - last_print > 10:
                last_print=time.time()
                parts=[f"{k}:{int(v)}s" for k,v in streak.items() if v>0]
                status=" ".join(parts) if parts else f"{current_cat}:{int(streak[current_cat])}s"
                print(f"  ⏱ {status} | vision: {vision_text[:75]}")
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("\nПока! Статистика:")
        for k,v in streak.items():
            if v>0: print(f"  {k}: {int(v//60)}м {int(v%60)}с")
        sys.exit(0)

if __name__ == "__main__":
    main()
