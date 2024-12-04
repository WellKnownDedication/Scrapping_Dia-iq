import os
from pathlib import Path
import shutil
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

def request(url):
    response = requests.get(url)
    print(f"response code {response.status_code} for {url}")

    if response.status_code != 200:
        print("unable to log in, waiting...")
        time.sleep(5)
        response = requests.get(url)
        print(f"response code {response.status_code} for {url}")
        if response.status_code != 200:
            return None

    return response

def process_main(url):
    response = request(url)
    if response.status_code != 200:
            return None, None

    soup = BeautifulSoup(response.content, "html.parser")
    main_content = soup.find("main", id="main") # find main body of a page

    article_div = main_content.find("div", class_="blog-isotope") # get section with articles

    # Extract article links
    article_links = []
    for a_tag in article_div.find_all("a", href=True):
        article_links.append(urljoin(url, a_tag["href"]))

    # Find the pagination section
    pagination = main_content.find("ul", class_="pagination justify-content-center")
    next_page = None
    if pagination:
        # Find all list items
        for li in pagination.find_all("li"):
            # Check if the item has the "icon-right-arrow" SVG inside
            svg_icon = li.find("svg", class_="icon-right-arrow")
            if svg_icon:  # This is the "next page" button
                next_button = li.find("a", href=True)
                if next_button:
                    next_page = urljoin(url, next_button["href"])

    return article_links, next_page

def save_metadata_to_txt(metadata, file_name):
    if not metadata:
        print("No metadata to save.")
        return

    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4, ensure_ascii=False)
    print(f"Metadata successfully saved to {file_name}")

def process_article(url,dirpath):
    response = request(url)
    if response.status_code != 200:
            return 

    soup = BeautifulSoup(response.content, "html.parser")

    script_tag = soup.find("script", class_="aioseo-schema") # get metadata section
    json_data = json.loads(script_tag.string) 

    for item in json_data.get("@graph", []):
        if item["@type"] == "BlogPosting":
                metadata = {
                "@type": item.get("@type"),
                "@id": item.get("@id"),
                "name": item.get("name"),
                "headline": item.get("headline"),
                "author": item.get("author", {}).get("@id") if item.get("author") else None,
                "publisher": item.get("publisher", {}).get("@id") if item.get("publisher") else None,
                "image": item.get("image", {}).get("url") if item.get("image") else None,
                "datePublished": item.get("datePublished"),
                "dateModified": item.get("dateModified"),
                "inLanguage": item.get("inLanguage"),
                "mainEntityOfPage": item.get("mainEntityOfPage", {}).get("@id"),
                "isPartOf": item.get("isPartOf", {}).get("@id"),
                "articleSection": item.get("articleSection"),
            }
    
    if metadata == None or datetime.fromisoformat(metadata["datePublished"]).year < 2015:
        return
    save_metadata_to_txt(metadata, f"{dirpath}/{metadata["name"]}: { datetime.fromisoformat(metadata["datePublished"]).year}.txt")
    metadata = None
    
def create_output_dir():
    dirpath = Path('output')
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(dirpath)
    
    os.makedirs(dirpath)
    return dirpath

def main():
    dirpath = create_output_dir()

    start_url = "https://dia-iq.lt/naujienos/"
    all_links = set()

    next_page = start_url
    while next_page:
        time.sleep(3)
        article_links, next_page = process_main(next_page)
        if article_links != None and next_page!= None:
            all_links.update(article_links)
            print(f"Articles saved: {len(all_links)}")

    for link in all_links:
        time.sleep(3)
        process_article(link,dirpath)
    
    print("\nAll articles have been processed.\n")

if __name__ == "__main__":
    main()
