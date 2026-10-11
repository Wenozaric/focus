from PIL import Image, ImageDraw
import pathlib, shutil
p = pathlib.Path(r"D:\coding\project\focus-nanny-electron\build")
p.mkdir(parents=True, exist_ok=True)
def draw_icon(size):
    img = Image.new('RGBA', (size,size), (0,0,0,0))
    d = ImageDraw.Draw(img)
    r = max(2, size//8)
    d.rounded_rectangle([0,0,size-1,size-1], radius=r, fill='#0f172a')
    pad = int(round(size * 0.26))
    bar = max(2, int(round(size * 0.135)))
    rad = max(1, bar//3)
    off = int(round(size * 0.025))  # оптический центр F (~2.5% вниз)
    d.rounded_rectangle([pad, pad+off, pad+bar, size-pad+off], radius=rad, fill='white')
    d.rounded_rectangle([pad, pad+off, size-pad, pad+bar+off], radius=rad, fill='white')
    mid_y0 = int(size*0.465) + off
    mid_x1 = int(pad + (size - 2*pad)*0.70)
    d.rounded_rectangle([pad, mid_y0, mid_x1, mid_y0+int(bar*0.88)], radius=rad, fill='white')
    return img
for sz in [16,32,48,64,128,256,512]:
    im = draw_icon(sz)
    im.save(p / f"icon-{sz}.png", "PNG")
    print(f"{sz} ok")
imgs = [Image.open(p/f"icon-{s}.png") for s in [16,32,48,256]]
imgs[3].save(p/"icon.ico", sizes=[(16,16),(32,32),(48,48),(256,256)])
shutil.copy(p/"icon-512.png", p/"icon.png")
print("ico+png ready")
