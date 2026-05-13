import os
import sys
import time
import requests
import re

sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

session = requests.Session()
session.headers.update(headers)


def get_with_retry(url, retries=10, timeout=30):
    for attempt in range(retries):
        try:
            return session.get(url, timeout=timeout)
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise
            wait = min(2 ** attempt, 60)
            print(f'Red: reintentando en {wait}s ({e})')
            time.sleep(wait)


books_counter = 0
page_url = "https://gutendex.com/books/?languages=es"
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '100libros')
os.makedirs(out_path, exist_ok=True)
files = os.listdir(out_path)
books_counter = len(files)
while books_counter < 100 and page_url:
    response = get_with_retry(page_url).json()

    for book in response['results']:
        if books_counter >= 100:
            break

        title = book['title']
        clean_title = re.sub(r'[<>:"/\\|?*;]', '', title)[:150].rstrip()
        formats = book['formats']
        txt_url = formats.get('text/plain; charset=utf-8') or \
                  formats.get('text/plain; charset=us-ascii') or \
                  formats.get('text/plain')

        if txt_url:
            if clean_title + '.txt' not in files:
                print(f'Descargando: {books_counter} - {clean_title}')
                filepath = os.path.join(out_path, f"{clean_title}.txt")

                try:
                    txt_content = get_with_retry(txt_url).text
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(txt_content)
                    files.append(clean_title + '.txt')
                    books_counter += 1
                except Exception as e:
                    print(f'Error descargando {clean_title}: {e}')
            else:
                print(f'Ya existe: {clean_title}')
        else:
            print(f'Sin formato txt: {clean_title}')

    page_url = response.get('next')
    if page_url:
        time.sleep(2)

print(f'Listo. Total libros: {books_counter}')
