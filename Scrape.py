import requests
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from tqdm.asyncio import tqdm

MAX_CONCURRENT = 5  # limit simultaneous downloads to avoid getting rate-limited

URL = "https://timarit.is/?q=t%C3%B6lubla%C3%B0&from=01.01.1990&to=31.12.1999&publicationId=58&textLanguage=&sort=date&isLongSnippets=false&isBeygingar=false&isAdvanced=false&size=100&page=0"
OUTPUT_DIR = "Src"


def fetch_image_urls(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    containers = soup.select("div.box-item.animation-top a figure img")

    urls = []
    for img in containers:
        alt = img.get("alt")
        src = img.get("src")
        img_id_str = src.split("/")[-1].strip()
        img_id = int(img_id_str) - 1
        print(img_id)
        urls.append((alt, f"https://timarit.is/files/{img_id}"))

    return urls


async def download_jpeg(session, url, output_path, semaphore):
    async with semaphore:
        async with session.get(url) as resp:
            resp.raise_for_status()

            total = int(resp.headers.get("Content-Length", 0))
            chunk_size = 1024

            with open(output_path, "wb") as f:
                with tqdm(total=total, unit="B", unit_scale=True, desc=output_path, leave=True) as progress:
                    async for chunk in resp.content.iter_chunked(chunk_size):
                        f.write(chunk)
                        progress.update(len(chunk))


async def download_many(urls):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    async with aiohttp.ClientSession() as session:
        tasks = [
            download_jpeg(session, url[1], f"{OUTPUT_DIR}/{url[0]}.jpg", semaphore)
            for url in urls
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    urls = fetch_image_urls(URL)
    asyncio.run(download_many(urls))
