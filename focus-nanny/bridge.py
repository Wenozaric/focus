# -*- coding: utf-8 -*-
import sys, json, time, threading, yaml, base64, io
from pathlib import Path
from collections import defaultdict
from datetime import datetime
try: sys.stdout.reconfigure(encoding="utf-8")
except: pass
ROOT=Path(__file__).parent
sys.path.insert(0, str(ROOT))
import psutil, mss as mss_module
from PIL import Image
try:
 import win32gui, win32process; HAS_WIN32=True
except: HAS_WIN32=False

def get_win():
 if HAS_WIN32:
  try:
   h=win32gui.GetForegroundWindow()
   if not h: return None,None,""
   _,pid=win32process.GetWindowThreadProcessId(h)
   t=win32gui.GetWindowText(h) or ""
   try: exe=psutil.Process(pid).name()
   except: exe=""
   return pid,exe,t
  except: return None,None,""
 else:
  try:
   from AppKit import NSWorkspace  # type: ignore  # pyright: ignore[reportMissingImports]
   app=NSWorkspace.sharedWorkspace().frontmostApplication()
   if app is None: return None,None,""
   exe=app.localizedName() or app.bundleIdentifier() or ""
   title=exe
   return None,exe,title
  except: return None,"Finder",""
try:
 import ollama; HAS_OLLAMA=True
 try: OLLAMA_CLIENT=ollama.Client(host="http://127.0.0.1:11434", trust_env=False, timeout=120)
 except: OLLAMA_CLIENT=ollama.Client(host="http://127.0.0.1:11434", timeout=120)
except: HAS_OLLAMA=False; OLLAMA_CLIENT=None

CFG_PATH=ROOT/"config.yaml"
SESSION_PATH=ROOT/"session.json"

def load_cfg():
 with open(CFG_PATH,encoding="utf-8") as f: return yaml.safe_load(f)
def save_cfg(c):
 with open(CFG_PATH,"w",encoding="utf-8") as f: yaml.safe_dump(c,f,allow_unicode=True,sort_keys=False)
def classify(title,exe,cfg):
 el=(exe or "").lower(); tl=(title or "").lower()
 games=[g.lower() for g in cfg.get("games",[])]
 if any(g==el or g in el for g in games): return "game"
 if any(k in tl for k in ["dota","cs2","valorant","minecraft","gta","elden ring","cyberpunk"]):
  if el not in ["chrome.exe","msedge.exe","firefox.exe",""] and el.endswith(".exe"): return "game"
 if "youtube" in tl:
  edu=[k.lower() for k in cfg.get("youtube_edu_keywords",[])]
  if any(k in tl for k in edu): return "youtube_edu"
  return "youtube"
 work=[k.lower() for k in cfg.get("work_keywords",[])]
 if any(k in tl or k in el for k in work): return "work"
 if not title.strip(): return "idle"
 return "other"

cfg=load_cfg()
today=datetime.now().strftime("%Y-%m-%d")
totals=defaultdict(float)
try:
 import json as _j
 if SESSION_PATH.exists():
  data=_j.loads(SESSION_PATH.read_text(encoding="utf-8"))
  for k,v in data.get(today,{}).items(): totals[k]=float(v)
except: pass
vision_text="ещё не смотрели"; vision_tag="other"; verdict="—"
current_cat="other"
running=True

def save_session():
 try:
  import json as _j
  data={}
  if SESSION_PATH.exists():
   try: data=_j.loads(SESSION_PATH.read_text(encoding="utf-8"))
   except: data={}
  data[today]=dict(totals)
  SESSION_PATH.write_text(_j.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
 except: pass

def emit():
 msg={"type":"tick","today":today,"totals":dict(totals),"currentCat":current_cat,"exe":cur_exe,"title":cur_title,"visionText":vision_text,"verdict":verdict,"visionTag":vision_tag}
 sys.stdout.write(json.dumps(msg,ensure_ascii=False)+"\n"); sys.stdout.flush()

def stdin_loop():
 global cfg, vision_text, verdict, vision_tag
 for line in sys.stdin:
  try:
   m=json.loads(line)
   if m.get("type")=="set_limits":
    cfg["limits"]["game_minutes"]=int(m.get("game",30))
    cfg["limits"]["youtube_total_minutes"]=int(m.get("youtube",30))
    cfg["limits"]["nag_interval_minutes"]=int(m.get("nag",5))
    cfg["voice_volume"]=int(m.get("volume",35))/100
    save_cfg(cfg)
   elif m.get("type")=="vision_now":
    threading.Thread(target=do_vision,daemon=True).start()
  except: pass

def do_vision():
 global vision_text, verdict, vision_tag
 try:
  if not HAS_OLLAMA or OLLAMA_CLIENT is None:
   vision_text="vision disabled"; verdict="vision disabled"; return
  with mss_module.MSS() as sct:
   img=sct.grab(sct.monitors[1])
   pil=Image.frombytes("RGB",img.size,img.bgra,"raw","BGRX")
   pil.thumbnail((640,640),Image.LANCZOS)
   buf=io.BytesIO(); pil.save(buf,format="JPEG",quality=62)
   b64=base64.b64encode(buf.getvalue()).decode()
  r=OLLAMA_CLIENT.chat(model=cfg.get("vision_model","moondream"),messages=[{"role":"user","content":"Describe briefly.","images":[b64]}],options={"temperature":0.3,"num_predict":80})
  try: txt=r["message"]["content"].strip() if isinstance(r,dict) else r.message.content.strip()
  except: txt=str(r)[:400]
  vision_text=txt or "A screen"
  prompt=f'Окно:"{cur_title[:120]}" exe:{cur_exe} скрин:"{txt[:200]}" -> [WORK]|[YOUTUBE_EDU]|[YOUTUBE]|[GAME]|[OTHER] 1 фраза.'
  r2=OLLAMA_CLIENT.chat(model=cfg.get("chat_model","llama3.1:8b"),messages=[{"role":"user","content":prompt}],options={"temperature":0.2,"num_predict":40})
  try: v=r2["message"]["content"].strip() if isinstance(r2,dict) else r2.message.content.strip()
  except: v=str(r2)[:300]
  verdict=v
  import re as _re
  m=_re.search(r"\[(WORK|YOUTUBE_EDU|YOUTUBE|GAME|OTHER)\]",v)
  vision_tag=m.group(1).lower() if m else "other"
 except Exception as e:
  vision_text=f"vision error: {e}"

threading.Thread(target=stdin_loop,daemon=True).start()
check=cfg.get("check_interval",3)
import time as _t
cur_exe=""; cur_title=""
last_vision=0
vision_interval=cfg.get("vision_interval",90)
while running:
 pid,exe,title=get_win()
 cur_exe=exe or ""; cur_title=title or ""
 cat=classify(title,exe,cfg)
 current_cat=cat
 totals[cat]+=check/60
 if _t.time()-last_vision>vision_interval and cfg.get("enable_vision",True):
  last_vision=_t.time(); threading.Thread(target=do_vision,daemon=True).start()
 emit()
 if int(_t.time())%10==0: save_session()
 _t.sleep(check)
