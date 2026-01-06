# Web scraping module. Implements searching for AnkerGames (Direct) and FitGirl Repacks (Torrents).
import requests
from bs4 import BeautifulSoup
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
