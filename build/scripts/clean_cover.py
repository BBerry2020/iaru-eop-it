import cv2, numpy as np, sys
src, out, dbg = sys.argv[1], sys.argv[2], sys.argv[3]
im = cv2.imread(src)
h, w = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
H, S, V = hsv[...,0], hsv[...,1], hsv[...,2]
bg = np.median(im[0:150].reshape(-1,3), axis=0)
ytop = int(h * 0.392)
core = ((H < 50) & (S > 40)).astype(np.uint8)
core[ytop:] = 0
near = cv2.dilate(core, np.ones((5,5),np.uint8), iterations=6) > 0
# within the text neighbourhood, everything that is not a clean circle line becomes background
circle = (np.abs(H-95) <= 3) & (V > 190) & (S < 235)
mask = (near & ~circle).astype(np.float32)
# logo box: flat fill too
x0, x1, y0, y1 = int(w*0.83), int(w*0.98), int(h*0.78), int(h*0.965)
box = hsv[y0:y1, x0:x1]
dev2 = ((np.abs(box[...,0]-95) > 3) | (box[...,1] < 200)).astype(np.uint8)*255
logo = cv2.morphologyEx(cv2.dilate(dev2, np.ones((5,5),np.uint8), iterations=4), cv2.MORPH_OPEN, np.ones((15,15),np.uint8))
logo = cv2.dilate(logo, np.ones((5,5),np.uint8), iterations=4)
mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], logo/255.0)
soft = cv2.GaussianBlur(mask, (0,0), 2.5)
soft = np.clip(soft*1.6, 0, 1)[..., None]
res = (im*(1-soft) + bg[None,None,:]*soft).astype(np.uint8)
cv2.imwrite(dbg, (soft[...,0]*255).astype(np.uint8))
res = res[10:-10, 10:-10]  # toglie il filo bianco ai bordi dell'immagine originale
cv2.imwrite(out, res, [cv2.IMWRITE_JPEG_QUALITY, 93])
print("bg BGR", bg)
