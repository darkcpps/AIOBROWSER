# Web scraping module. Implements searching for AnkerGames (Direct) and FitGirl Repacks (Torrents).
import requests
from bs4 import BeautifulSoup
import json
import html as html_lib
import re
from urllib.parse import quote, unquote

# =========================================================================
# CONFIGURATION & CONSTANTS
# =========================================================================
import concurrent.futures

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# =========================================================================
# FITGIRL MODULE (TORRENTS)
# =========================================================================
def search_fitgirl(query):
    # 1. Get basic results from search page
    initial_results = scrape_search_results(f"https://fitgirl-repacks.site/?s={query}", "FitGirl")

    # 2. Enrich with images and magnets (in parallel)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_game = {executor.submit(enrich_fitgirl_game, game): game for game in initial_results}
        
        for future in concurrent.futures.as_completed(future_to_game):
            game = future_to_game[future]
            try:
                data = future.result()
                if data:
                    game['image'] = data.get('image')
                    game['magnet'] = data.get('magnet')
            except Exception as e:
                print(f"[DEBUG] Error enriching {game['title']}: {e}")

    # 3. FILTER: Only keep results that have a magnet link
    games_only = [game for game in initial_results if game.get('magnet')]

    return games_only

def enrich_fitgirl_game(game):
    data = {"image": None, "magnet": None}
    try:
        resp = requests.get(game['link'], headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 1. Look for Image
            content = soup.find(class_='entry-content')
            if content:
                img = content.find('img')
                if img:
                    data['image'] = img.get('data-src') or img.get('src')
                
                # 2. Look for Magnet Link
                magnet = content.find('a', href=lambda h: h and h.startswith('magnet:?'))
                if magnet:
                    data['magnet'] = magnet['href']
    except:
        pass
    return data

def scrape_search_results(url, source):
    results = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            articles = soup.find_all('article')
            for article in articles:
                title_tag = article.find(class_="entry-title")
                if title_tag and title_tag.find('a'):
                    link = title_tag.find('a')
                    results.append({
                        "title": link.text.strip(),
                        "link": link['href'],
                        "image": None, # Will be filled later
                        "source": source
                    })
    except Exception as e:
        print(f"[DEBUG] Error {source}: {e}")
    return results

def scrape_magnet(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            magnet = soup.find('a', href=lambda href: href and href.startswith("magnet:"))
            if magnet:
                return magnet['href']
    except Exception as e:
        print(f"[DEBUG] Magnet scrape error: {e}")
    return None

# =========================================================================
# ANKERGAMES MODULE (DIRECT)
# =========================================================================
class AnkerClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://ankergames.net/",
            "X-Requested-With": "XMLHttpRequest"
        })
        self.base_url = "https://ankergames.net"

    def search(self, query):
        clean_name = query.strip()
        search_url = f"{self.base_url}/search/{quote(clean_name)}"
        print(f"[DEBUG] Searching Anker: {search_url}")
        
        results = []
        try:
            resp = self.session.get(search_url)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # AnkerGames usually lists results in a grid or list
            # We look for links that look like game pages
            candidates = soup.find_all('a', href=True)
            print(f"[DEBUG] Found {len(candidates)} candidates")

            seen_links = set()

            for a in candidates:
                href = a['href']
                title = a.get('aria-label') or a.text.strip()
                if title:
                    # Remove "view details" case-insensitively
                    title = re.sub(r'\s*-?\s*view\s+details\s*', '', title, flags=re.IGNORECASE).strip()
                    
                    if "/game/" in href:
                        if href in seen_links: continue
                        
                        full_link = href
                        if not full_link.startswith('http'):
                            full_link = self.base_url + full_link
                        
                        # Find image (logic based on browser subagent)
                        image_url = None
                        parent = a.find_parent()
                        if parent:
                            img_tag = parent.find('img')
                            if img_tag:
                                image_url = img_tag.get('data-src') or img_tag.get('src')
                                if image_url and not image_url.startswith('http'):
                                    image_url = self.base_url + image_url
                        
                        # Avoid duplicates
                        seen_links.add(href)
                        
                        # clean title
                        if not title: title = href.split('/')[-1].replace('-', ' ').title()

                        results.append({
                            "title": title,
                            "link": full_link,
                            "image": image_url,
                            "source": "AnkerGames"
                        })
            
            return results
        except Exception as e:
            print(f"[DEBUG] Anker Search Error: {e}")
            return []

    def get_download_link(self, game_page_url):
        try:
            print(f"[DEBUG] Fetching game page: {game_page_url}")
            resp = self.session.get(game_page_url)
            soup = BeautifulSoup(resp.text, 'html.parser')

            csrf_token = soup.find('meta', {'name': 'csrf-token'})
            if csrf_token: csrf_token = csrf_token['content']
            else: return None, "CSRF Token not found"

            game_id_match = re.search(r'generateDownloadUrl\((\d+)\)', resp.text)
            if not game_id_match: return None, "Game ID not found"
            
            game_id = game_id_match.group(1)
            
            post_url = f"{self.base_url}/generate-download-url/{game_id}"
            payload = {"g-recaptcha-response": "development-mode"}
            
            self.session.headers.update({
                "X-CSRF-TOKEN": csrf_token,
                "Content-Type": "application/json",
                "Referer": game_page_url
            })
            
            resp_post = self.session.post(post_url, json=payload)
            if resp_post.status_code == 200:
                data = resp_post.json()
                if data.get('success') and data.get('download_url'):
                    return data['download_url'], None
            
            return None, f"API Error or Failed: {resp_post.status_code}"
            
        except Exception as e:
            return None, str(e)

    # -------------------------------------------------------------------------
    # ANKER RESOLVER: Deep Link Extraction
    # -------------------------------------------------------------------------
    def resolve_final_link(self, url):
        try:
            # Follow redirects first
            resp = self.session.get(url, stream=True, allow_redirects=True)
            content_type = resp.headers.get('Content-Type', '').lower()
            final_url = resp.url
            
            # If it's a file
            if 'text/html' not in content_type:
                filename = None
                cd = resp.headers.get('Content-Disposition')
                if cd:
                    fnames = re.findall(r'filename\*?=([^;]+)', cd)
                    if fnames:
                        filename = fnames[0].strip().strip('"').strip("'")
                        if "UTF-8''" in filename:
                            filename = filename.split("UTF-8''")[-1]
                return final_url, filename

            # If HTML, scrape
            print(f"[DEBUG] Hit intermediate page: {final_url}")
            html_content = resp.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. Meta Refresh
            meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'^refresh$', re.I)})
            if meta_refresh:
                content = meta_refresh.get('content', '')
                if 'url=' in content.lower():
                    redirect_url = re.split(r'url=', content, flags=re.I)[-1].strip()
                    if redirect_url: return redirect_url, None

            # 2. JS Redirects
            patterns = [
                r'window\.location\.href\s*=\s*["\'](.*?)["\']',
                r'window\.location\s*=\s*["\'](.*?)["\']',
                r'location\.href\s*=\s*["\'](.*?)["\']',
                r'location\.replace\s*\(\s*["\'](.*?)["\']\s*\)',
                r'window\.open\s*\(\s*["\'](.*?)["\']',
                r'var\s+downloadUrl\s*=\s*["\'](.*?)["\']',
                r'let\s+downloadUrl\s*=\s*["\'](.*?)["\']',
                r'const\s+downloadUrl\s*=\s*["\'](.*?)["\']',
                r'var\s+url\s*=\s*["\'](.*?)["\']'
            ]
            for p in patterns:
                match = re.search(p, html_content)
                if match and "http" in match.group(1):
                    return match.group(1), None

            # 3. Download Button
            btn_id = soup.find(id=re.compile(r'download', re.I))
            if btn_id and btn_id.name == 'a' and btn_id.get('href'): return btn_id['href'], None

            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.text.strip().lower()
                if "download" in text or "click here" in text:
                     if "ankergames" not in href or "download" in href:
                        if href and href != "#" and not href.startswith("javascript"):
                            return href, None
            
            # 4. Reveal Button
            reveal_btn = soup.find('a', class_=re.compile(r'download-btn-reveal'))
            if reveal_btn and reveal_btn.get('href') and "dlproxy" in reveal_btn['href']:
                return reveal_btn['href'], None

            # 5. Deep Scan
            deep = re.findall(r'(https?://(?:[\w-]+\.)?dlproxy\.uk/[^\'"\s<>]+)', html_content)
            if deep: return deep[0], None

            # 6. Archive Pattern
            archive = re.findall(r'["\'](https?://.*?\.(?:zip|rar|7z|exe|iso))["\']', html_content, re.I)
            if archive:
                 for link in archive:
                     if "assets" not in link and "jquery" not in link: return link, None

            # 7. Alpine variable
            dl_var = re.search(r'downloadUrl\s*[:=]\s*["\'](.*?)["\']', html_content)
            if dl_var:
                try:
                    curr = unquote(dl_var.group(1))
                    if "dlproxy" in curr or "http" in curr: return curr, None
                except: pass

            # 8. x-data hidden URL (User Provided Strategy)
            x_data_match = re.search(r"x-data=\"downloadPage\('([^']+)'", html_content)
            if x_data_match:
                try:
                    encoded_url = x_data_match.group(1)
                    final_url = unquote(encoded_url)
                    print(f"[DEBUG] Found x-data URL: {final_url}")
                    return final_url, None
                except Exception as e:
                    print(f"[DEBUG] Error parsing x-data: {e}")

            return final_url, None

        except Exception as e:
            print(f"[DEBUG] Resolution failed: {e}")
            return url, None


# =========================================================================
# AXEKIN MODULE (ROMS)
# =========================================================================
AXEKIN_BASE_URL = "https://www.axekin.com"


def _parse_inertia_data_page(html_text):
    """
    Axekin is an Inertia app; the page payload is stored in a data-page attribute.
    Returns a dict or None.
    """
    try:
        match = re.search(r'data-page="([^"]+)"', html_text)
        if not match:
            return None
        data = html_lib.unescape(match.group(1))
        return json.loads(data)
    except Exception as e:
        print(f"[DEBUG] Axekin parse error: {e}")
        return None


def search_axekin(query, platform=None, page=1):
    """
    Scrapes Axekin ROM entries and returns a list of downloadable items.
    Each returned item matches the UI's card shape:
      {title, link, image, source, size, platforms, page_url}
    """
    clean_query = (query or "").strip()
    if not clean_query:
        return []

    search_url = f"{AXEKIN_BASE_URL}/games?search={quote(clean_query)}&page={page}"
    results = []
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []

        page_data = _parse_inertia_data_page(resp.text)
        if not page_data:
            return []

        games = page_data.get("props", {}).get("data", []) or []
        desired_platform = (platform or "").strip().lower()

        for game in games:
            name = (
                game.get("name")
                or game.get("alternativeName")
                or game.get("slug")
                or "Unknown"
            )
            slug = game.get("slug") or ""
            platforms = game.get("platforms") or []
            if desired_platform and desired_platform != "any":
                platform_set = {str(p).lower() for p in platforms}
                if desired_platform not in platform_set:
                    continue

            cover_url = None
            cover = game.get("cover") or {}
            if isinstance(cover, dict):
                cover_url = cover.get("url")

            file_size = game.get("fileSize")
            download_links = game.get("downloadLinks") or []

            source = "Axekin"
            if platforms:
                source += " • " + ", ".join(str(p).upper() for p in platforms)

            page_url = (
                f"{AXEKIN_BASE_URL}/games/{slug}"
                if slug
                else f"{AXEKIN_BASE_URL}/games?search={quote(name)}"
            )

            for dl in download_links:
                if not isinstance(dl, dict):
                    continue
                link = dl.get("link")
                if not link:
                    continue
                label = (dl.get("label") or "").strip()
                title = name if not label else f"{name} ({label})"

                results.append(
                    {
                        "title": title,
                        "link": link,
                        "image": cover_url,
                        "source": source,
                        "size": file_size,
                        "platforms": platforms,
                        "page_url": page_url,
                    }
                )

    except Exception as e:
        print(f"[DEBUG] Error Axekin: {e}")

    return results

# =========================================================================
# MONKRUS MODULE (ADOBE SOFTWARE)
# =========================================================================
def search_monkrus(query):
    """
    Scrapes Monkrus search results.
    Each result is contained in a div.post, with a meta[itemprop="image_url"] tag for the thumbnail.
    """
    clean_query = quote(query.strip())
    search_url = f"https://w17.monkrus.ws/search?q={clean_query}"
    results = []
    
    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Each result is contained in a div.post element
            posts = soup.find_all('div', class_='post')
            
            for post in posts:
                # Find the title and link from h2.post-title a
                h2 = post.find('h2', class_='post-title')
                if not h2:
                    continue
                    
                a = h2.find('a')
                if not a or not a.get('href'):
                    continue
                    
                title = a.text.strip()
                link = a['href']
                
                if not link.startswith('http'):
                    link = "https://w17.monkrus.ws" + link
                
                # Extract image from meta[itemprop="image_url"] tag
                image_url = None
                meta_img = post.find('meta', attrs={'itemprop': 'image_url'})
                if meta_img and meta_img.get('content'):
                    image_url = meta_img['content']
                else:
                    # Fallback: try to find img in post-body
                    post_body = post.find('div', class_='post-body')
                    if post_body:
                        img = post_body.find('img')
                        if img:
                            image_url = img.get('src')
                    
                results.append({
                    "title": title,
                    "link": link,
                    "image": image_url,
                    "source": "Monkrus"
                })
    except Exception as e:
        print(f"[DEBUG] Monkrus Search Error: {e}")
        
    return results

def resolve_monkrus_to_torrent(monkrus_url):
    """
    Resolves a Monkrus page to the final .torrent link on Uztracker.
    """
    print(f"[DEBUG] Resolving Monkrus URL: {monkrus_url}")
    try:
        # 1. Fetch Monkrus page
        print("[DEBUG] Fetching Monkrus page...")
        resp = requests.get(monkrus_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            print(f"[DEBUG] Error: Failed to fetch Monkrus page (Status: {resp.status_code})")
            return None, f"Failed to fetch Monkrus page (Status: {resp.status_code})"
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 2. Find Uztracker link
        print("[DEBUG] Finding Uztracker link in Monkrus page content...")
        uz_link_tag = soup.find('a', href=lambda h: h and 'uztracker.net' in h)
        if not uz_link_tag:
            print("[DEBUG] Error: Uztracker link not found. Available links:")
            # Log some links for debugging if not found
            for a in soup.find_all('a', href=True)[:10]:
                print(f"  - {a['href']}")
            return None, "Uztracker link not found on Monkrus page. Try a different version (2025/2026)"
            
        uz_url = uz_link_tag['href']
        print(f"[DEBUG] Found Uztracker URL: {uz_url}")
        
        # 3. Fetch Uztracker page
        print("[DEBUG] Fetching Uztracker page...")
        resp_uz = requests.get(uz_url, headers=HEADERS, timeout=10)
        if resp_uz.status_code != 200:
            print(f"[DEBUG] Error: Failed to fetch Uztracker page (Status: {resp_uz.status_code})")
            return None, f"Failed to fetch Uztracker page (Status: {resp_uz.status_code})"
            
        soup_uz = BeautifulSoup(resp_uz.text, 'html.parser')
        
        # 4. Find .torrent download link
        print("[DEBUG] Searching for '.torrent' download link on Uztracker...")
        dl_tag = soup_uz.find('a', class_='dw-dl') or soup_uz.find('a', href=lambda h: h and h.startswith('dl.php?id='))
        
        if dl_tag and dl_tag.get('href'):
            final_dl = dl_tag['href']
            if not final_dl.startswith('http'):
                final_dl = "https://uztracker.net/" + final_dl
            print(f"[DEBUG] Success! Found .torrent URL: {final_dl}")
            return final_dl, None
            
        print("[DEBUG] Error: No download link found with class 'dw-dl' or 'dl.php' pattern.")
        return None, "Torrent download link not found on Uztracker"
        
    except Exception as e:
        print(f"[DEBUG] Critical Exception in resolution: {str(e)}")
        return None, str(e)
