import sys, importlib.util
from multiprocessing import Pool
sys.argv = ["x", "/home/claude/reels/faq/ov"]
spec = importlib.util.spec_from_file_location("fr", "/home/claude/reels/faq/faq_reel.py")
fr = importlib.util.module_from_spec(spec); spec.loader.exec_module(fr)
def job(i):
    fr.overlay(i / fr.FPS).save(f"/home/claude/reels/faq/ov/{i:04d}.png", compress_level=1)
if __name__ == "__main__":
    fr.sfx("/home/claude/reels/faq/sfx.wav")
    with Pool(8) as p:
        p.map(job, range(fr.NF), chunksize=8)
    print("frames", fr.NF)
