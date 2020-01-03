import os, glob, subprocess, concurrent.futures, multiprocessing


def magickworker(f):
    print("Processing " + os.path.basename(f))
    p = subprocess.Popen(["magick", "convert", f, "-format", "webp", "-quality", "100", "-define", "webp:lossless=true", "-define", "webp:method=6", os.path.basename(f)[:-4] + ".webp"], shell = True)
    p.wait()

with concurrent.futures.ThreadPoolExecutor(max_workers=(multiprocessing.cpu_count() + 1)) as executor:
    for png in glob.iglob("*.png"):
        executor.submit(magickworker, png)
    executor.shutdown(wait=True)
