# -*- coding: utf-8 -*-
import os, sys, yaml, time, threading, re, base64, io, json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass
os.environ["NO_PROXY"]="localhost,127.0.0.1,::1"
os.environ["no_proxy"]="localhost,127.0.0.1,::1"
import psutil, win32gui, win32process
import mss as mss_module
from PIL import Image
import tkinter as tk
from tkinter import ttk
try:
 import ollama; HAS_OLLAMA=True
 try: OLLAMA_CLIENT=ollama.Client(host="http://127.0.0.1:11434", trust_env=False, timeout=120)
 except: OLLAMA_CLIENT=ollama.Client(host="http://127.0.0.1:11434", timeout=120)
except: HAS_OLLAMA=False; OLLAMA_CLIENT=None
try: import pyttsx3; HAS_TTS=True
except: HAS_TTS=False
ROOT=Path(__file__).parent
CFG_PATH=ROOT/"config.yaml"
SESSION_PATH=ROOT/"session.json"
BG="#f1f5f9"; CARD="#ffffff"; CARD2="#f8fafc"; BORDER="#e2e8f0"; BORDER_A="#e2e8f0"
FG="#0f172a"; MUTED="#334155"; SUB="#64748b"; ACCENT="#0ea5e9"; ACCENT_HOVER="#0284c7"; TRACK_BG="#e2e8f0"; RADIUS=12
G_WORK="#10b981"; G_YT_EDU="#0ea5e9"; G_YT_FUN="#f59e0b"; G_GAME="#f43f5e"; G_OTHER="#cbd5e1"; G_IDLE="#94a3b8"
def load_cfg():
 with open(CFG_PATH,encoding="utf-8") as f: return yaml.safe_load(f)
def save_cfg(c):
 with open(CFG_PATH,"w",encoding="utf-8") as f: yaml.safe_dump(c,f,allow_unicode=True,sort_keys=False)
def get_win():
 try:
  h=win32gui.GetForegroundWindow()
  if not h: return None,None,""
  _,pid=win32process.GetWindowThreadProcessId(h)
  t=win32gui.GetWindowText(h) or ""
  try: exe=psutil.Process(pid).name()
  except: exe=""
  return pid,exe,t
 except: return None,None,""
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
class VisionWatcher:
 def __init__(self,cfg):
  self.cfg=cfg; self.enabled=cfg.get("enable_vision",True)
  self.model=cfg.get("vision_model","moondream")
  self.judge_model=cfg.get("chat_model","llama3.1:8b"); self.use_llm=cfg.get("enable_llm_judge", False)
  self.last_desc="еще не смотрели"; self.last_verdict="еще не смотрели"; self.last_tag="other"; self.last_time=0
 def cap(self,ms=640):
  with mss_module.MSS() as sct:
   img=sct.grab(sct.monitors[1])
   pil=Image.frombytes("RGB",img.size,img.bgra,"raw","BGRX")
   pil.thumbnail((ms,ms), Image.LANCZOS)
   buf=io.BytesIO(); pil.save(buf,format="JPEG",quality=62)
   return base64.b64encode(buf.getvalue()).decode()
 def describe(self):
  if not self.enabled or not HAS_OLLAMA or OLLAMA_CLIENT is None: return "vision disabled"
  try:
   b64=self.cap()
   r=OLLAMA_CLIENT.chat(model=self.model, messages=[{"role":"user","content":"Describe the screenshot briefly.","images":[b64]}], options={"temperature":0.3,"num_predict":80,"num_ctx":512,"num_thread":4,"repeat_penalty":1.1})
   try: txt=r["message"]["content"].strip() if isinstance(r,dict) else r.message.content.strip()
   except: txt=str(r)[:500]
   if not txt:
    r2=OLLAMA_CLIENT.chat(model=self.model, messages=[{"role":"user","content":"Describe the screenshot briefly.","images":[b64]}], options={"temperature":0.3,"num_predict":80,"num_ctx":512,"num_thread":4})
    try: txt=r2["message"]["content"].strip() if isinstance(r2,dict) else r2.message.content.strip()
    except: txt=""
   if not txt: txt="A computer screen"
   self.last_desc=txt; return txt
  except Exception as e: return f"vision error: {e}"
 def judge(self,title,exe,desc):
  hint=classify(title,exe,self.cfg)
  prompt=(f'Окно: "{title[:160]}" exe:{exe} | Скрин: "{desc[:260]}" | хинт:{hint}\n'
          'Вердикт: WORK/YOUTUBE_EDU/YOUTUBE/GAME/OTHER. Заголовок важнее скрина: tutorial/урок/python/course->EDU, иначе YOUTUBE.\n'
          'Ответ: 1-2 предл. по-русски + тег [WORK]|[YOUTUBE_EDU]|[YOUTUBE]|[GAME]|[OTHER].')
  if not getattr(self,"use_llm", False):
    raise RuntimeError("llm judge disabled - heuristic")
  try:
   r=OLLAMA_CLIENT.chat(model=self.judge_model, messages=[{"role":"user","content":prompt}], options={"temperature":0.2,"num_predict":60,"num_ctx":512,"num_thread":2})
   try: txt=r["message"]["content"].strip() if isinstance(r,dict) else r.message.content.strip()
   except: txt=str(r)[:400]
   if not txt: raise ValueError("empty")
   self.last_verdict=txt; self.last_time=time.time()
   import re as _re
   m=_re.search(r"\[(WORK|YOUTUBE_EDU|YOUTUBE|GAME|OTHER)\]",txt)
   tag=m.group(1).lower().replace("youtube_fun","youtube") if m else "other"
   self.last_tag=tag; return txt,tag
  except Exception:
   tl=title.lower(); low=(title+" "+desc).lower()
   if any(k in low for k in ["cs2","dota","minecraft","valorant","gta","elden","steam"]): tag="game"
   elif "youtube" in low:
    edu=[k.lower() for k in self.cfg.get("youtube_edu_keywords",[])]
    if any(k in tl for k in edu): tag="youtube_edu"
    elif any(k in low for k in ["tutorial","лекция","урок","python","course","lesson"]): tag="youtube_edu"
    else: tag="youtube"
   elif any(k in low for k in ["code","editor","vs code"]): tag="work"
   else: tag="other"
   fb=f"{desc} -> {tag} [{tag.upper()}]"
   self.last_verdict=fb; self.last_tag=tag; self.last_time=time.time()
   return fb,tag
 def analyze(self,title,exe):
  d=self.describe()
  if "vision error" in d or "disabled" in d: return d,"other"
  v,t=self.judge(title,exe,d)
  return v,t

def load_session():
 p=SESSION_PATH
 if p.exists():
  try:
   with open(p,encoding="utf-8") as f: return json.load(f)
  except: pass
 return {}
def save_session(d):
 try:
  with open(SESSION_PATH,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
 except: pass
def _round_rect(can,x0,y0,x1,y1,r,fill):
 try:
  can.create_rectangle(x0+r,y0,x1-r,y1, fill=fill, outline="", width=0)
  can.create_rectangle(x0,y0+r,x1,y1-r, fill=fill, outline="", width=0)
  can.create_oval(x0,y0,x0+2*r,y0+2*r, fill=fill, outline="")
  can.create_oval(x1-2*r,y0,x1,y0+2*r, fill=fill, outline="")
  can.create_oval(x0,y1-2*r,x0+2*r,y1, fill=fill, outline="")
  can.create_oval(x1-2*r,y1-2*r,x1,y1, fill=fill, outline="")
 except: pass
class Switch(tk.Canvas):
 def __init__(self,parent,var,command=None,width=36,height=18):
  super().__init__(parent,width=width,height=height,bg=CARD,highlightthickness=0,bd=0)
  self.var=var; self.cmd=command; self.w=width; self.h=height
  self.bind("<Button-1>",self.toggle); self.var.trace_add("write",lambda *a:self.redraw()); self.redraw()
 def toggle(self,_=None):
  self.var.set(not self.var.get())
  if self.cmd: self.cmd()
 def redraw(self):
  self.delete("all"); on=self.var.get(); bg=G_WORK if on else "#e2e8f0"; knob="white"
  _round_rect(self,0,0,self.w,self.h,9,bg)
  x= self.w-14 if on else 2
  self.create_oval(x,2,x+14,16,fill=knob,outline="")
class FluentSlider(tk.Canvas):
 def __init__(self,parent,frm,to,var,fmt,save_cb,width=220,height=22):
  super().__init__(parent,width=width,height=height,bg=CARD,highlightthickness=0,bd=0)
  self.frm=frm;self.to=to;self.var=var;self.fmt=fmt;self.save_cb=save_cb
  self.drag=False;self.hover=False
  self.bind("<Button-1>",self._down);self.bind("<B1-Motion>",self._drag);self.bind("<ButtonRelease-1>",self._up)
  self.bind("<Enter>",lambda e:(setattr(self,"hover",True),self.redraw()))
  self.bind("<Leave>",lambda e:(setattr(self,"hover",False),self.redraw()))
  self.var.trace_add("write",lambda *a:self.redraw());self.redraw()
 def _pos(self): return (self.var.get()-self.frm)/(self.to-self.frm) if self.to!=self.frm else 0
 def _set(self,x):
  w=self.winfo_width() or 220;pad=10;track=w-2*pad;pct=max(0,min(1,(x-pad)/track if track else 0));v=int(round(self.frm+pct*(self.to-self.frm)));self.var.set(v)
  if self.save_cb: self.save_cb(v)
 def _down(self,e): self.drag=True;self._set(e.x);self.redraw()
 def _drag(self,e):
  if self.drag: self._set(e.x);self.redraw()
 def _up(self,e): self.drag=False;self.redraw()
 def redraw(self):
  self.delete("all");w=self.winfo_width() or 220;h=self.winfo_height() or 22;pad=10;cy=h//2;th=4
  _round_rect(self,pad,cy-th//2,w-pad,cy+th//2,2,TRACK_BG)
  pct=self._pos();fw=int((w-2*pad)*pct)
  if fw>0:
   col=ACCENT if self.hover or self.drag else FG
   _round_rect(self,pad,cy-th//2,pad+fw,cy+th//2,2,col)
  cx=pad+int((w-2*pad)*pct)
  shadow="#cbd5e1" if not self.drag else "#94a3b8"
  self.create_oval(cx-9,cy-9,cx+9,cy+9,fill=shadow,outline="",width=0)
  fill="white";outline=ACCENT if self.hover or self.drag else "#cbd5e1"
  self.create_oval(cx-8,cy-8,cx+8,cy+8,fill=fill,outline=outline,width=1.5)

class Stepper(tk.Frame):
 def __init__(self,parent,var,frm,to,fmt,save_cb):
  super().__init__(parent,bg=CARD)
  self.var=var;self.frm=frm;self.to=to;self.fmt=fmt;self.save_cb=save_cb
  self.btn_m=tk.Button(self,text="−",command=self.dec,bg=CARD,fg=FG,activebackground=CARD2,font=("Segoe UI Variable",10,"bold"),bd=0,padx=8,pady=2,cursor="hand2",highlightthickness=1,highlightbackground=BORDER,relief="flat",width=2)
  self.btn_m.pack(side="left",padx=(0,6))
  self.lab=tk.Label(self,text=fmt.format(var.get()),fg=FG,bg=CARD,font=("Consolas",9,"bold"),width=9,anchor="center")
  self.lab.pack(side="left")
  self.btn_p=tk.Button(self,text="+",command=self.inc,bg=CARD,fg=FG,activebackground=CARD2,font=("Segoe UI Variable",10,"bold"),bd=0,padx=8,pady=2,cursor="hand2",highlightthickness=1,highlightbackground=BORDER,relief="flat",width=2)
  self.btn_p.pack(side="left",padx=(6,0))
  self.var.trace_add("write",lambda *a:self.sync());self.sync()
 def sync(self): self.lab.configure(text=self.fmt.format(int(round(self.var.get()))))
 def dec(self):
  v=max(self.frm,int(round(self.var.get()))-1);self.var.set(v)
  if self.save_cb: self.save_cb(v)
 def inc(self):
  v=min(self.to,int(round(self.var.get()))+1);self.var.set(v)
  if self.save_cb: self.save_cb(v)

class App(tk.Tk):
 def __init__(self):
  super().__init__()
  self.cfg=load_cfg()
  self.title("Focus")
  self.geometry("900x920")
  self.minsize(780,720)
  self.configure(bg=BG)
  style=ttk.Style(self)
  try: style.theme_use("clam")
  except: pass
  style.configure("TFrame", background=CARD)
  style.configure("TLabel", background=CARD, foreground=FG, font=("Segoe UI Variable",9))
  style.configure("TButton", font=("Segoe UI Variable",8,"bold"), padding=6)
  style.configure("Title.TLabel", font=("Segoe UI Variable",12,"bold"), foreground=FG)
  style.configure("Horizontal.TScale", background=CARD, troughcolor="#f1f5f9", sliderlength=16)
  sess=load_session()
  self.today=datetime.now().strftime("%Y-%m-%d")
  d0=sess.get(self.today, {})
  if "youtube_fun" in d0: d0["youtube"]=d0.get("youtube",0)+d0.pop("youtube_fun")
  self.total=defaultdict(float, d0)
  self.streak=defaultdict(float)
  self.current_cat="other"; self.last_nag=0
  self.vision_text="еще не смотрели"; self.vision_verdict="еще не смотрели"; self.vision_tag="other"
  self.vision=VisionWatcher(self.cfg)
  self.running=True; self.banner=None
  self._cur_exe=""; self._cur_title=""
  self._build()
  self.after(600, self._tick)
  self.after(1200, self._vision_loop)
  self.protocol("WM_DELETE_WINDOW", self.on_close)
 def _build(self):
  canv=tk.Canvas(self, bg=BG, highlightthickness=0)
  sb=ttk.Scrollbar(self, orient="vertical", command=canv.yview)
  canv.configure(yscrollcommand=sb.set)
  canv.pack(side="left", fill="both", expand=True)
  try: sb.pack(side="right", fill="y")
  except: pass
  outer=tk.Frame(canv, bg=BG)
  win=canv.create_window((0,0), window=outer, anchor="nw")
  def sync_w(e): canv.itemconfig(win, width=e.width)
  canv.bind("<Configure>", sync_w)
  def on_conf(e): canv.configure(scrollregion=canv.bbox("all"))
  outer.bind("<Configure>", on_conf)
  def on_wheel(e):
   try:
    if e.delta: canv.yview_scroll(int(-e.delta/120), "units")
    elif e.num==4: canv.yview_scroll(-1,"units")
    elif e.num==5: canv.yview_scroll(1,"units")
   except: pass
  canv.bind_all("<MouseWheel>", on_wheel)
  canv.bind_all("<Button-4>", on_wheel)
  canv.bind_all("<Button-5>", on_wheel)
  hdr=tk.Frame(outer, bg=CARD)
  hdr.pack(fill="x", padx=20, pady=(20,16))
  hdr.configure(highlightthickness=1, highlightbackground=BORDER_A, bd=0)
  hdr_inner=tk.Frame(hdr, bg=CARD)
  hdr_inner.pack(fill="x", padx=22, pady=16)
  logo=tk.Canvas(hdr_inner, width=40, height=40, bg=CARD, highlightthickness=0, bd=0)
  logo.pack(side="left")
  _round_rect(logo, 0,0,40,40,12, FG)
  logo.create_text(20,20, text="FN", fill="white", font=("Segoe UI Variable",10,"bold"))
  lt=tk.Frame(hdr_inner, bg=CARD)
  lt.pack(side="left", padx=14)
  tk.Label(lt, text="FOCUS", fg=FG, bg=CARD, font=("Segoe UI Variable",13,"bold")).pack(anchor="w")
  tk.Label(lt, text="Локальный контроль фокуса  \u00b7  moondream  \u00b7  приватно", fg=MUTED, bg=CARD, font=("Segoe UI Variable",8)).pack(anchor="w", pady=(2,0))
  pill=tk.Frame(hdr_inner, bg=CARD2)
  pill.pack(side="right", pady=2)
  pill.configure(highlightthickness=1, highlightbackground=BORDER_A, bd=0)
  self.dot=tk.Label(pill, text="\u25cf", fg=G_IDLE, bg=CARD2, font=("Segoe UI Variable",12))
  self.dot.pack(side="left", padx=(12,4), pady=8)
  self.state_lbl=tk.Label(pill, text="idle", fg=FG, bg=CARD2, font=("Consolas",9,"bold"))
  self.state_lbl.pack(side="left", padx=(0,8))
  self.badge=tk.Label(pill, text="OTHER", fg="white", bg=G_OTHER, font=("Segoe UI Variable",7,"bold"), padx=10, pady=3)
  self.badge.pack(side="left", padx=(0,10), pady=6)
  grid=tk.Frame(outer, bg=BG)
  grid.pack(fill="x", padx=20, pady=0)
  today_card=tk.Frame(grid, bg=CARD)
  today_card.pack(side="left", fill="both", expand=True, padx=(0,8))
  today_card.configure(highlightthickness=1, highlightbackground=BORDER_A, bd=0)
  th=tk.Frame(today_card, bg=CARD)
  th.pack(fill="x", padx=18, pady=(18,10))
  tk.Label(th, text="\u0421\u0435\u0433\u043e\u0434\u043d\u044f", fg=FG, bg=CARD, font=("Segoe UI Variable",11,"bold")).pack(side="left")
  tk.Label(th, text="\u00b7  \u0432\u0441\u0435\u0433\u043e \u0432\u0440\u0435\u043c\u0435\u043d\u0438", fg=MUTED, bg=CARD, font=("Segoe UI Variable",8)).pack(side="left", padx=(6,0))
  self.total_lbl=tk.Label(th, text="0\u043c \u0432\u0441\u0435\u0433\u043e", fg=FG, bg=CARD, font=("Consolas",9,"bold"))
  self.total_lbl.pack(side="right")
  self.hero_lbl=tk.Label(today_card, text="0\u0447 00\u043c", fg=FG, bg=CARD, font=("Segoe UI Variable",30,"bold"))
  self.hero_lbl.pack(anchor="w", padx=18)
  tk.Label(today_card, text="\u043e\u0431\u0449\u0435\u0435 \u0432\u0440\u0435\u043c\u044f \u0437\u0430 \u0441\u0435\u0433\u043e\u0434\u043d\u044f", fg=MUTED, bg=CARD, font=("Segoe UI Variable",8)).pack(anchor="w", padx=18, pady=(0,10))
  bar_wrap=tk.Frame(today_card, bg=CARD)
  bar_wrap.pack(fill="x", padx=18, pady=(0,16))
  self.bars={}
  dot_map={"work":G_WORK,"youtube_edu":G_YT_EDU,"youtube":"#f59e0b","game":G_GAME,"idle":G_IDLE,"other":G_OTHER}
  for key,label in [("work","\u0420\u0430\u0431\u043e\u0442\u0430"),("youtube_edu","YouTube \u00b7 \u0443\u0447\u0451\u0431\u0430"),("youtube","YouTube"),("game","\u0418\u0433\u0440\u044b"),("idle","\u041f\u0440\u043e\u0441\u0442\u043e\u0439"),("other","\u041f\u0440\u043e\u0447\u0435\u0435")]:
   col=dot_map.get(key, G_OTHER)
   row=tk.Frame(bar_wrap, bg=CARD)
   row.pack(fill="x", pady=4)
   left=tk.Frame(row, bg=CARD)
   left.pack(side="left")
   dot=tk.Canvas(left, width=8, height=8, bg=CARD, highlightthickness=0, bd=0)
   dot.pack(side="left", padx=(0,8))
   dot.create_oval(0,0,8,8, fill=col, outline="")
   tk.Label(left, text=label, fg=FG, bg=CARD, font=("Segoe UI Variable",9), width=16, anchor="w").pack(side="left")
   can=tk.Canvas(row, height=6, bg=CARD, highlightthickness=0, bd=0)
   can.pack(side="left", fill="x", expand=True, padx=10)
   val=tk.Label(row, text="0\u043c", fg=MUTED, bg=CARD, font=("Consolas",8,"bold"), width=7, anchor="e")
   val.pack(side="left")
   pct=tk.Label(row, text="0%", fg=MUTED, bg=CARD, font=("Segoe UI Variable",8), width=5, anchor="e")
   pct.pack(side="left", padx=(6,0))
   self.bars[key]=(can,val,pct,col)
  side=tk.Frame(grid, bg=CARD)
  side.pack(side="left", fill="both", expand=True, padx=(8,0))
  side.configure(highlightthickness=1, highlightbackground=BORDER_A, bd=0)
  tk.Label(side, text="\u0421\u0435\u0439\u0447\u0430\u0441", fg=FG, bg=CARD, font=("Segoe UI Variable",10,"bold")).pack(anchor="w", padx=18, pady=(18,6))
  tk.Label(side, text="\u0430\u043a\u0442\u0438\u0432\u043d\u043e\u0435 \u043e\u043a\u043d\u043e", fg=MUTED, bg=CARD, font=("Segoe UI Variable",7)).pack(anchor="w", padx=18)
  self.exe_lbl=tk.Label(side, text="\u2014", fg=MUTED, bg=CARD, font=("Consolas",8), anchor="w", wraplength=320, justify="left")
  self.exe_lbl.pack(fill="x", padx=18, pady=(14,0))
  self.title_lbl=tk.Label(side, text="\u2014", fg=FG, bg=CARD, font=("Segoe UI Variable",9), anchor="w", wraplength=320, justify="left")
  self.title_lbl.pack(fill="x", padx=18, pady=(4,0))
  act=tk.Frame(side, bg=CARD)
  act.pack(fill="x", padx=18, pady=14)
  def mk_btn(parent, text, cmd, primary=False):
   bgc=ACCENT if primary else CARD
   fgc="white" if primary else FG
   bd=BORDER if not primary else ACCENT
   b=tk.Button(parent, text=text, command=cmd, bg=bgc, fg=fgc, activebackground=ACCENT_HOVER if primary else CARD2, activeforeground=fgc, font=("Segoe UI Variable",9,"bold"), bd=0, padx=16, pady=8, cursor="hand2", highlightthickness=1, highlightbackground=bd, relief="flat")
   def on_enter(e): b.configure(bg=ACCENT_HOVER if primary else "#f8fafc")
   def on_leave(e): b.configure(bg=bgc)
   b.bind("<Enter>", on_enter)
   b.bind("<Leave>", on_leave)
   return b
  mk_btn(act, "\u0421\u043a\u0440\u0438\u043d \u0441\u0435\u0439\u0447\u0430\u0441", self.trigger_vision, primary=True).pack(side="left", padx=(0,8))
  mk_btn(act, "\u0422\u0435\u0441\u0442 \u0431\u0430\u043d\u043d\u0435\u0440\u0430", self.test_nag, primary=False).pack(side="left")
  sys_card=tk.Frame(outer, bg=CARD)
  sys_card.pack(fill="x", padx=20, pady=10)
  sys_card.configure(highlightthickness=1, highlightbackground=BORDER_A, bd=0)
  vh=tk.Frame(sys_card, bg=CARD)
  vh.pack(fill="x", padx=18, pady=(18,10))
  tk.Label(vh, text="\u0421\u0438\u0441\u0442\u0435\u043c\u0430", fg=FG, bg=CARD, font=("Segoe UI Variable",10,"bold")).pack(side="left")
  tk.Label(vh, text="moondream  \u00b7  640px  \u00b7  80 \u0442\u043e\u043a\u0435\u043d\u043e\u0432  \u00b7  90\u0441", fg=MUTED, bg=CARD, font=("Segoe UI Variable",7)).pack(side="left", padx=(8,0))
  self.vision_time=tk.Label(vh, text="\u0435\u0449\u0451 \u043d\u0435 \u0441\u043c\u043e\u0442\u0440\u0435\u043b\u0438", fg=MUTED, bg=CARD, font=("Consolas",7))
  self.vision_time.pack(side="right")
  def mono_box(parent):
   o=tk.Frame(parent, bg=CARD2)
   o.pack(fill="x", padx=18, pady=(0,8))
   o.configure(highlightthickness=1, highlightbackground=BORDER_A, bd=0)
   return o
  tk.Label(sys_card, text="\u0421\u043a\u0440\u0438\u043d", fg=MUTED, bg=CARD, font=("Segoe UI Variable",7,"bold")).pack(anchor="w", padx=18, pady=(0,4))
  f1=mono_box(sys_card)
  self.desc_txt=tk.Text(f1, wrap="word", height=2, bg=CARD2, fg=FG, font=("Segoe UI Variable",9), bd=0, padx=12, pady=10, highlightthickness=0, relief="flat", spacing1=2)
  self.desc_txt.pack(fill="x", expand=True)
  self.desc_txt.insert("1.0","\u0435\u0449\u0451 \u043d\u0435 \u0441\u043c\u043e\u0442\u0440\u0435\u043b\u0438 \u2014 \u0441\u043a\u0440\u0438\u043d \u043a\u0430\u0436\u0434\u044b\u0435 90\u0441")
  self.desc_txt.configure(state="disabled")
  tk.Label(sys_card, text="\u0412\u0435\u0440\u0434\u0438\u043a\u0442", fg=MUTED, bg=CARD, font=("Segoe UI Variable",7,"bold")).pack(anchor="w", padx=18, pady=(0,4))
  f2=mono_box(sys_card)
  self.verdict_txt=tk.Text(f2, wrap="word", height=2, bg=CARD2, fg=FG, font=("Segoe UI Variable",9), bd=0, padx=12, pady=10, highlightthickness=0, relief="flat", spacing1=2)
  self.verdict_txt.pack(fill="x", expand=True)
  self.verdict_txt.insert("1.0","\u2014")
  self.verdict_txt.configure(state="disabled")
  self.title_meta=tk.Label(sys_card, text="\u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a: \u2014", fg=MUTED, bg=CARD, font=("Consolas",7), anchor="w", justify="left", wraplength=760)
  self.title_meta.pack(fill="x", padx=18, pady=(4,14))
  setf=tk.Frame(outer, bg=CARD)
  setf.pack(fill="x", padx=20, pady=(0,10))
  setf.configure(highlightthickness=1, highlightbackground=BORDER_A, bd=0)
  tk.Label(setf, text="\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438", fg=FG, bg=CARD, font=("Segoe UI Variable",10,"bold")).pack(anchor="w", padx=18, pady=(18,6))
  tk.Label(setf, text="\u043b\u0438\u043c\u0438\u0442\u044b \u0438 \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u044f", fg=MUTED, bg=CARD, font=("Segoe UI Variable",7)).pack(anchor="w", padx=18, pady=(0,10))
  grid2=tk.Frame(setf, bg=CARD)
  grid2.pack(fill="x", padx=18, pady=(0,8))
  grid2.columnconfigure(1, weight=1)
  def add_slider(parent,label,frm,to,kp,default,fmt="{} \u043c\u0438\u043d",row=0):
   tk.Label(parent, text=label, fg=FG, bg=CARD, font=("Segoe UI Variable",9)).grid(row=row, column=0, sticky="w", padx=0, pady=14)
   var=tk.IntVar(value=default)
   def save_cb(v):
    ks=kp.split("."); d=self.cfg
    for k in ks[:-1]: d=d.setdefault(k,{})
    d[ks[-1]]=int(v); save_cfg(self.cfg)
   holder=tk.Frame(parent,bg=CARD)
   holder.grid(row=row, column=1, sticky="ew", padx=12)
   holder.columnconfigure(0,weight=1)
   sl=FluentSlider(holder,frm,to,var,fmt,save_cb)
   sl.grid(row=0,column=0,sticky="ew")
   Stepper(parent,var,frm,to,fmt,save_cb).grid(row=row,column=2,sticky="e",padx=(8,0))
   return var
  lim=self.cfg.get("limits",{})
  add_slider(grid2,"\u041b\u0438\u043c\u0438\u0442 \u0438\u0433\u0440\u044b",1,60,"limits.game_minutes",lim.get("game_minutes",30),row=0)
  add_slider(grid2,"\u041b\u0438\u043c\u0438\u0442 YouTube",1,90,"limits.youtube_total_minutes",lim.get("youtube_total_minutes",30),row=1)
  add_slider(grid2,"\u041f\u0430\u0443\u0437\u0430 \u00ab\u0430\u044f\u044f\u0439\u00bb",1,30,"limits.nag_interval_minutes",lim.get("nag_interval_minutes",5),row=2)
  vr=tk.IntVar(value=int(float(self.cfg.get("voice_volume",0.35))*100))
  tk.Label(grid2, text="\u0413\u0440\u043e\u043c\u043a\u043e\u0441\u0442\u044c \u0433\u043e\u043b\u043e\u0441\u0430", fg=FG, bg=CARD, font=("Segoe UI Variable",9)).grid(row=3, column=0, sticky="w", pady=14)
  def vol_cb(v): self.cfg["voice_volume"]=int(v)/100; save_cfg(self.cfg)
  vh2=tk.Frame(grid2,bg=CARD); vh2.grid(row=3,column=1,sticky="ew",padx=12); vh2.columnconfigure(0,weight=1)
  vsl=FluentSlider(vh2,0,100,vr,"{}%",vol_cb)
  vsl.grid(row=0,column=0,sticky="ew")
  Stepper(grid2,vr,0,100,"{}%",vol_cb).grid(row=3,column=2,sticky="e",padx=(8,0))
  tog=tk.Frame(setf, bg=CARD)
  tog.pack(fill="x", padx=18, pady=(10,18))
  self.voice_var=tk.BooleanVar(value=self.cfg.get("enable_voice",False))
  self.gui_var=tk.BooleanVar(value=self.cfg.get("enable_gui_popup",True))
  self.vision_var=tk.BooleanVar(value=self.cfg.get("enable_vision",True))
  def toggle(k,v):
   self.cfg[k]=bool(v.get())
   save_cfg(self.cfg)
   self.vision.enabled=bool(self.vision_var.get())
  row_sw=tk.Frame(tog, bg=CARD)
  row_sw.pack(fill="x")
  for txt,var,key in [("\u041e\u0437\u0432\u0443\u0447\u0438\u0432\u0430\u0442\u044c \u00ab\u0430\u044f\u044f\u0439\u00bb",self.voice_var,"enable_voice"),("\u0412\u0441\u043f\u043b\u044b\u0432\u0430\u0442\u044c \u043e\u043a\u043d\u043e\u043c",self.gui_var,"enable_gui_popup"),("\u0410\u043d\u0430\u043b\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0441\u043a\u0440\u0438\u043d",self.vision_var,"enable_vision")]:
   fr=tk.Frame(row_sw, bg=CARD)
   fr.pack(side="left", padx=(0,20))
   tk.Label(fr, text=txt, fg=FG, bg=CARD, font=("Segoe UI Variable",8)).pack(side="left", padx=(0,8))
   Switch(fr, var, command=lambda k=key,v=var: toggle(k,v)).pack(side="left")
  foot=tk.Frame(outer, bg=BG)
  foot.pack(fill="x", padx=20, pady=(6,18))
  tk.Label(foot, text="Focus \u00b7 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u043e  \u00b7  \u043f\u0440\u0438\u0432\u0430\u0442\u043d\u043e", fg=MUTED, bg=BG, font=("Segoe UI Variable",7)).pack(side="left")
  ttk.Button(foot, text="\u0421\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0441\u0435\u0433\u043e\u0434\u043d\u044f", command=self.reset_today).pack(side="right")

 def _vision_loop(self):
  if not self.running: return
  def _run():
   exe,title=self._cur_exe,self._cur_title
   try:
    txt,tag=self.vision.analyze(title,exe)
    self.vision_text=self.vision.last_desc; self.vision_verdict=txt; self.vision_tag=tag
    self.after(0, self._render_vision)
   except Exception as e:
    self.vision_text=f"vision error: {e}"
  threading.Thread(target=_run, daemon=True).start()
  self.after(int(self.cfg.get("vision_interval",90)*1000), self._vision_loop)
 def _render_vision(self):
  for w in (self.desc_txt,self.verdict_txt): w.configure(state="normal")
  self.desc_txt.delete("1.0","end"); self.desc_txt.insert("1.0", self.vision_text)
  self.verdict_txt.delete("1.0","end"); self.verdict_txt.insert("1.0", self.vision_verdict)
  for w in (self.desc_txt,self.verdict_txt): w.configure(state="disabled")
  self.vision_time.configure(text=datetime.now().strftime("%H:%M:%S")+" \u00b7 "+self.vision_tag)
  self.title_meta.configure(text=f"\u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a: {(self._cur_title[:110] or '\u2014')}")
  col={"work":G_WORK,"youtube_edu":G_YT_EDU,"youtube":G_OTHER,"game":G_GAME,"idle":G_IDLE,"other":G_OTHER}.get(self.vision_tag,G_OTHER)
  self.dot.configure(fg=col); self.badge.configure(bg=col, text=self.vision_tag.upper()); self.state_lbl.configure(text=self.vision_tag)
 def _tick(self):
  if not self.running: return
  _,exe,title=get_win()
  self._cur_exe=exe or ""; self._cur_title=title or ""
  cat=classify(title,exe,self.cfg)
  if self.vision.enabled and time.time()-self.vision.last_time < 90 and self.vision.last_tag not in ("other",""):
   vt=self.vision.last_tag
   if vt in ("youtube","youtube_edu","game","work"):
    if vt=="youtube_edu" and cat in ("youtube","youtube_edu"):
     cat="youtube_edu"
    elif vt=="youtube" and cat in ("youtube","youtube_edu"):
     if cat!="youtube_edu": cat="youtube"
    elif vt=="game":
     cat=vt
    elif vt=="work" and cat in ("other","idle"):
     cat="work"
    elif vt=="idle" and cat=="idle":
     cat="idle"
  self.current_cat=cat
  colors={"work":G_WORK,"youtube_edu":G_YT_EDU,"youtube":G_OTHER,"game":G_GAME,"idle":G_IDLE,"other":G_OTHER}
  col=colors.get(cat,G_OTHER)
  self.dot.configure(fg=col); self.state_lbl.configure(text=cat)
  self.badge.configure(text=cat.upper(), bg=col)
  self.exe_lbl.configure(text=exe or "\u2014")
  self.title_lbl.configure(text=(title[:72]+"\u2026" if len(title)>72 else title) or "\u2014")
  ci=float(self.cfg.get("check_interval",3))
  self.total[cat]+=ci/60.0
  for k in list(self.streak.keys()):
   if k!=cat: self.streak[k]=0
  self.streak[cat]+=ci/60.0
  save_session({self.today: dict(self.total)})
  self._render_bars(); self._maybe_nag(cat)
  self.log_lbl.configure(text=f"{datetime.now().strftime('%H:%M:%S')}  {cat}  | {exe}  |  {title[:48]}")
  self.after(int(ci*1000), self._tick)
 def _render_bars(self):
  tot=sum(self.total.values()) or 0.001
  self.total_lbl.configure(text=f"{int(round(tot))}м всего  ·  streak {int(round(self.streak.get(self.current_cat,0)))}м  {self.current_cat}")
  for key,(can,val,pct_col,col) in self.bars.items():
   m=self.total.get(key,0); pct=m/tot
   can.delete("all")
   w=can.winfo_width() or 340
   h=6; r=3
   can.configure(height=h, bg=CARD)
   _round_rect(can, 0, 0, w, h, r, TRACK_BG)
   fw=int(w*pct)
   if fw>0:
    if fw>=2*r:
     _round_rect(can, 0, 0, fw, h, r, col)
    else:
     can.create_oval(0,0,fw,h, fill=col, outline="")
   val.configure(text=f"{m:.1f}м" if m<60 else f"{m/60:.1f}ч")
   pct_col.configure(text=f"{int(round(pct*100))}%")
   pct_col.configure(foreground=FG if key==self.current_cat else SUB)
   val.configure(foreground=FG if key==self.current_cat else MUTED)
 def _maybe_nag(self,cat):
  now=time.time()
  lim=self.cfg.get("limits",{})
  thr=None
  if cat=="game": thr=lim.get("game_minutes",30)
  elif cat=="youtube": thr=lim.get("youtube_total_minutes",30)
  else: return
  need_global=self.total.get(cat,0) >= thr
  need_streak=self.streak.get(cat,0) >= 1.0
  if not (need_global and need_streak): return
  if now - self.last_nag < lim.get("nag_interval_minutes",5)*60: return
  self.last_nag=now
  msg=f"\u041b\u0438\u043c\u0438\u0442! \u0422\u044b \u0443\u0436\u0435 {int(round(self.total[cat]))} \u043c\u0438\u043d {cat} \u2014 \u043f\u043e\u0440\u0430 \u0432\u0435\u0440\u043d\u0443\u0442\u044c\u0441\u044f \u043a \u0444\u043e\u043a\u0443\u0441\u0443. "
  self.show_banner(msg); self.speak(msg)
 def show_banner(self,msg):
  if not self.cfg.get("enable_gui_popup",True): return
  if self.banner:
   try: self.banner.destroy()
   except: pass
  self.banner=tk.Toplevel(self)
  self.banner.overrideredirect(True); self.banner.attributes("-topmost", True)
  self.banner.configure(bg="#1a1a1e")
  frm=tk.Frame(self.banner, bg="#dc2626", padx=18, pady=14); frm.pack(fill="both", expand=True)
  tk.Label(frm, text="ЛИМИТ!", fg="white", bg="#dc2626", font=("Segoe UI Variable",16,"bold")).pack(anchor="w")
  tk.Label(frm, text=msg, fg="white", bg="#dc2626", font=("Segoe UI Variable",10), wraplength=420, justify="left").pack(anchor="w", pady=(6,10))
  ttk.Button(frm, text="Понял, работаю", command=self.banner.destroy).pack(anchor="e")
  try: self.bell()
  except: pass
  self.lift(); self.focus_force(); self.banner.lift(); self.banner.focus_force()
  sw=self.winfo_screenwidth(); bw=520; bh=140
  self.banner.geometry(f"{bw}x{bh}+{(sw-bw)//2}+80")
  self.after(14000, lambda: self.banner and self.banner.destroy() if self.banner and self.banner.winfo_exists() else None)
 def speak(self,msg):
  if not self.cfg.get("enable_voice",False) or not HAS_TTS: return
  def _t():
   try:
    e=pyttsx3.init(); e.setProperty("rate",170); e.setProperty("volume", float(self.cfg.get("voice_volume",0.35))); e.say(msg); e.runAndWait()
   except: pass
  threading.Thread(target=_t, daemon=True).start()
 def trigger_vision(self):
  def _run():
   exe,title=self._cur_exe,self._cur_title
   self.vision_time.configure(text="смотрю…")
   txt,tag=self.vision.analyze(title,exe)
   self.vision_text=self.vision.last_desc; self.vision_verdict=txt; self.vision_tag=tag
   self.after(0, self._render_vision)
  threading.Thread(target=_run, daemon=True).start()
 def test_nag(self): self.show_banner("Тест: окно лимита — поверх окон и со звуком.")
 def reset_today(self):
  self.total=defaultdict(float); self.streak=defaultdict(float); save_session({self.today: {}}); self._render_bars()
 def on_close(self):
  self.running=False; save_session({self.today: dict(self.total)}); self.destroy()
if __name__=="__main__":
 App().mainloop()