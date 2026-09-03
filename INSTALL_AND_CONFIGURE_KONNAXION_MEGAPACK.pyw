from __future__ import annotations
import json,os,shutil,subprocess,sys,threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog,messagebox,ttk
PACK_ROOT=Path(__file__).resolve().parent
DEFAULT_LEVELUP=r"C:\mycode\LevelUpDiag\LevelUpDiag"; DEFAULT_KONNAXION=r"C:\mycode\Konnaxion\Konnaxion"; DEFAULT_CAPSULE_MANAGER=r"C:\mycode\Konnaxion\Konnaxion_Capsule_Manager"
DIRS=("levelupdiag_core","konnaxion_diag","levels","scripts","launchers","docs","schemas","tests")
FILES=("levelupdiag.py","levelupdiag_manifest.json","levelupdiag.config.json","levelupdiag.config.example.json","README.md","RUN_KONNAXION_LEVELUPDIAG.bat","RUN_KONNAXION_LEVELUPDIAG.sh",".gitignore",".smartignore")
def install_and_configure(levelup,konnaxion,capsule_manager,capsule_file=''):
    levelup=Path(levelup).expanduser().resolve(); kx=Path(konnaxion).expanduser().resolve(); cm=Path(capsule_manager).expanduser().resolve()
    for p,n in ((levelup,'LevelUpDiag'),(kx,'Konnaxion'),(cm,'Capsule Manager')):
        if not p.is_dir(): raise FileNotFoundError(f'{n} introuvable: {p}')
    backup=levelup/'.levelupdiag-upgrade-backups'/('konnaxion-v3-'+datetime.now().strftime('%Y%m%d-%H%M%S')); backup.mkdir(parents=True)
    local=levelup/'levelupdiag.config.local.json'
    if local.exists(): shutil.copy2(local,backup/local.name)
    for d in DIRS:
        dst=levelup/d
        if dst.exists(): shutil.move(str(dst),str(backup/d))
        shutil.copytree(PACK_ROOT/d,dst)
    for f in FILES:
        src=PACK_ROOT/f; dst=levelup/f
        if dst.exists():
            (backup/f).parent.mkdir(parents=True,exist_ok=True); shutil.copy2(dst,backup/f)
        shutil.copy2(src,dst)
    cfg=json.loads((levelup/'levelupdiag.config.example.json').read_text(encoding='utf-8-sig')); cfg['target_repo_root']=str(kx); cfg['konnaxion']['capsule_manager_repo']=str(cm); cfg['konnaxion']['capsule_file']=capsule_file.strip()
    local.write_text(json.dumps(cfg,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return backup,local
def run_campaign(levelup,campaign):
    py=Path(sys.executable); py=py.with_name('python.exe') if py.name.lower()=='pythonw.exe' and py.with_name('python.exe').exists() else py
    return subprocess.Popen([str(py),str(levelup/'levelupdiag.py'),'run',campaign],cwd=str(levelup),creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0) if os.name=='nt' else 0)
class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Konnaxion LevelUpDiag v3 — upgrade + configuration'); self.geometry('920x560')
        self.l=tk.StringVar(value=DEFAULT_LEVELUP); self.k=tk.StringVar(value=DEFAULT_KONNAXION); self.c=tk.StringVar(value=DEFAULT_CAPSULE_MANAGER); self.f=tk.StringVar(); self.s=tk.StringVar(value='Prêt.')
        fr=ttk.Frame(self,padding=18); fr.pack(fill='both',expand=True); fr.columnconfigure(1,weight=1)
        ttk.Label(fr,text='Konnaxion LevelUpDiag v3 — moteur évolué + séquence Konnaxion',font=('Segoe UI',15,'bold')).grid(row=0,column=0,columnspan=3,sticky='w',pady=(0,16))
        for row,label,var in [(1,'LevelUpDiag',self.l),(2,'Konnaxion',self.k),(3,'Capsule Manager',self.c)]: self.pathrow(fr,row,label,var)
        ttk.Label(fr,text='Capsule (optionnel)').grid(row=4,column=0,sticky='w'); ttk.Entry(fr,textvariable=self.f).grid(row=4,column=1,sticky='ew'); ttk.Button(fr,text='Parcourir…',command=self.file).grid(row=4,column=2)
        ttk.Label(fr,text='Séquence connection-debug: N00 → N01 → N02 → N03 → N04 → N05 → N06 → N11\nLes anciens logs ne sont pas migrés; seules les preuves courantes sont conservées.',justify='left').grid(row=5,column=0,columnspan=3,sticky='w',pady=16)
        self.b=ttk.Button(fr,text='UPGRADER + CONFIGURER',command=self.install); self.b.grid(row=6,column=0,columnspan=3,sticky='ew',ipady=8)
        box=ttk.LabelFrame(fr,text='Diagnostics',padding=10); box.grid(row=7,column=0,columnspan=3,sticky='ew',pady=14)
        for i,(label,camp) in enumerate([('Source audit','source-audit'),('Auth debug','auth-debug'),('Connection debug','connection-debug'),('Full local','full-local')]): ttk.Button(box,text=label,command=lambda c=camp:self.run(c)).grid(row=0,column=i,sticky='ew',padx=4); box.columnconfigure(i,weight=1)
        ttk.Label(fr,textvariable=self.s,wraplength=850).grid(row=8,column=0,columnspan=3,sticky='w')
    def pathrow(self,fr,row,label,var):
        ttk.Label(fr,text=label).grid(row=row,column=0,sticky='w'); ttk.Entry(fr,textvariable=var).grid(row=row,column=1,sticky='ew'); ttk.Button(fr,text='Parcourir…',command=lambda:self.folder(var)).grid(row=row,column=2)
    def folder(self,var):
        x=filedialog.askdirectory(); var.set(x or var.get())
    def file(self):
        x=filedialog.askopenfilename(filetypes=[('Konnaxion capsule','*.kxcapsule'),('Tous','*.*')]); self.f.set(x or self.f.get())
    def install(self):
        self.b.configure(state='disabled'); self.s.set('Upgrade en cours…')
        def work():
            try: b,c=install_and_configure(self.l.get(),self.k.get(),self.c.get(),self.f.get()); self.after(0,lambda:self.ok(b,c))
            except Exception as e: self.after(0,lambda:self.err(e))
        threading.Thread(target=work,daemon=True).start()
    def ok(self,b,c): self.b.configure(state='normal'); self.s.set(f'Upgrade terminé. Backup: {b} | Config: {c}'); messagebox.showinfo('Terminé','Upgrade v3 terminé. Commence par Source audit.')
    def err(self,e): self.b.configure(state='normal'); self.s.set(f'Échec: {e}'); messagebox.showerror('Échec',str(e))
    def run(self,campaign):
        try: run_campaign(Path(self.l.get()).expanduser().resolve(),campaign); self.s.set(f'Campagne lancée: {campaign}')
        except Exception as e: self.err(e)
if __name__=='__main__': App().mainloop()
