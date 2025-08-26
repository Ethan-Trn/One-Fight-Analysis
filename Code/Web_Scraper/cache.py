import os, hashlib, tempfile, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

#Session is essetnially making a connection to the Internent Protcols
SESSION = requests.Session()
#This is where we store all our cache and we make sure it already is there
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

#This converts the html into a hash map key so that way we are sure it's distinct
#Kinda of like encrypting the website to somethign the cache would understand (KIND OF)
def _cache_path(url: str) -> str:
    key = hashlib.md5(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.html")

#This one essetniallys puts the url and the html inside of it into the cache folder if it wasn't already in there 
def _write_cache_atomic(path: str, data: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=CACHE_DIR, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp, path)

def fetch_cached(url: str, *, timeout: float = 20.0, polite_delay_on_miss: float = 0.2) -> str:
    #Checks if the url /html is already inside our cache file
    #if it is return the html (that's what f.read() does. f is the file from which we just opened and f.read is what's inside the folder)
    path = _cache_path(url)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    #if we didn't get it then what we do is we save that shit into our cache file
    resp = SESSION.get(url, timeout=timeout)
    resp.raise_for_status()
    html = resp.text
    _write_cache_atomic(path, html)
    if polite_delay_on_miss:
        time.sleep(polite_delay_on_miss)  # only on real network hit
    return html
#Parallel - Not that importnant to learn
def fetch_many_cached(urls, max_workers: int = 8, timeout: float = 20.0):
    out = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_cached, u, timeout=timeout): u for u in urls}
        for fut in as_completed(futs):
            u = futs[fut]
            try:
                out[u] = fut.result()
            except Exception as e:
                print(f"[fetch error] {u}: {e}")
    return out
