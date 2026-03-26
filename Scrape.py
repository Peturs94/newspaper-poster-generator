import requests
from bs4 import BeautifulSoup
import re
import aiohttp
import asyncio
from tqdm.asyncio import tqdm

url = "https://timarit.is/?q=t%C3%B6lubla%C3%B0&from=01.01.1990&to=31.12.1999&publicationId=58&textLanguage=&sort=date&isLongSnippets=false&isBeygingar=false&isAdvanced=false&size=100&page=0"   # <-- replace with your target page

# Fetch HTML
html = requests.get(url).text

# Parse HTML
soup = BeautifulSoup(html, "html.parser")

# Find all div elements with class "box-item animation-top"
containers = soup.select("div.box-item.animation-top a figure img")

# Regex to extract URL from style="background-image: url('...')"
url_pattern = re.compile(r"<img src=\"(.*)\" alt=\"(.*)\">")

urls = []

for img in containers:
    #print(img)
    #match = url_pattern.search(str(img))
    alt = img.get("alt")
    src = img.get("src")
    img_id_str = str.split(src, '/').pop().strip()
    img_id_full_q = int(img_id_str) -1
    print(img_id_full_q)
    urls.append((alt, f"https://timarit.is/files/{img_id_full_q}"))
    #print(f"{alt} - {src}")


async def download_jpeg(session, url, output_path):
    async with session.get(url) as resp:
        resp.raise_for_status()

        total = int(resp.headers.get("Content-Length", 0))
        chunk_size = 1024

        with open(output_path, "wb") as f:
            progress = tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                desc=output_path,
                leave=True
            )

            async for chunk in resp.content.iter_chunked(chunk_size):
                f.write(chunk)
                progress.update(len(chunk))

            progress.close()

async def download_many(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, url in enumerate(urls):
            output_name = f"{url[0]}.jpg"
            tasks.append(download_jpeg(session, url[1], f"SRC/{output_name}"))

        await asyncio.gather(*tasks)

asyncio.run(download_many(urls))