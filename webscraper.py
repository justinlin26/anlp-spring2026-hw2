import os
import json
import time
import logging
import threading
import concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, List
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRAPE_URLS_7 = {
    "Government": "https://www.pittsburghpa.gov/Home",
    "Symphony": "https://www.pittsburghsymphony.org",
    "cmu_wikipedia": "https://en.wikipedia.org/wiki/Carnegie_Mellon_University",
    "pittsburgh_wikipedia": "https://en.wikipedia.org/wiki/Pittsburgh",
    "pittsburgh_history_wikipedia": "https://en.wikipedia.org/wiki/History_of_Pittsburgh",
    "pittsburgh_gov": "https://www.pittsburghpa.gov/Home",
    "britannica_pittsburgh": "https://www.britannica.com/place/Pittsburgh",
    "visit_pittsburgh": "https://www.visitpittsburgh.com",
    "cmu_about": "https://www.cmu.edu/about/",
    "cmu_history": "https://www.cmu.edu/about/history.html",
    "pittsburgh_events": "https://pittsburgh.events/",
    "downtown_events": "https://downtownpittsburgh.com/events/",
    "cmu_events": "https://events.cmu.edu",
    "pittsburgh_symphony": "https://www.pittsburghsymphony.org",
    "pittsburgh_opera": "https://pittsburghopera.org",
    "cultural_trust": "https://trustarts.org",
    "carnegie_museums": "https://carnegiemuseums.org",
    "heinz_history_center": "https://www.heinzhistorycenter.org",
    "the_frick": "https://www.thefrickpittsburgh.org",
    "food_festivals": "https://www.visitpittsburgh.com/events-festivals/food-festivals/",
    "picklesburgh": "https://www.picklesburgh.com/",
    "taco_fest": "https://www.pghtacofest.com/",
    "restaurant_week": "https://pittsburghrestaurantweek.com/",
    "little_italy_days": "https://littleitalydays.com",
    "banana_split_fest": "https://bananasplitfest.com",
    "pirates": "https://www.mlb.com/pirates",
    "steelers": "https://www.steelers.com",
    "penguins": "https://www.nhl.com/penguins/",
    "visit_pgh_sports": "https://www.visitpittsburgh.com/things-to-do/pittsburgh-sports-teams/",
    "ri": "https://www.ri.cmu.edu/",
    "the_tartan": "https://the-tartan.org/",
    "wiki_alumni": "https://en.wikipedia.org/wiki/List_of_Carnegie_Mellon_University_people",
    "food": "https://www.goodfoodpittsburgh.com/",
    "brookline": "https://brooklineconnection.com/",
    "discover": "https://www.discovertheburgh.com/",
  "City of Pittsburgh": "https://pittsburghpa.gov",
  "Pittsburgh City Code (Municode)": "https://library.municode.com/pa/pittsburgh",
  "United States Census Bureau": "https://www.census.gov",
  "Allegheny County": "https://www.alleghenycounty.us",
  "Pittsburgh Parks Conservancy": "https://pittsburghparks.org",
  "Carnegie Museums of Pittsburgh": "https://carnegiemuseums.org",
  "Carnegie Museum of Art": "https://carnegieart.org",
  "Carnegie Museum of Natural History": "https://carnegiemnh.org",
  "The Andy Warhol Museum": "https://www.warhol.org",
  "Kamin Science Center": "https://carnegiesciencecenter.org",
  "Heinz History Center": "https://www.heinzhistorycenter.org",
  "The Frick Pittsburgh": "https://www.thefrickpittsburgh.org",
  "Mattress Factory": "https://mattress.org",
  "Roberto Clemente Museum": "https://clementemuseum.com",
  "Randyland": "https://randyland.club/",
  "American Jewish Museum (JCC)": "https://jccpgh.org",
  "Pittsburgh Cultural Trust": "https://trustarts.org",
  "Pittsburgh Opera": "https://www.pittsburghopera.org",
  "Pittsburgh Symphony Orchestra": "https://pittsburghsymphony.org",
  "Pittsburgh Ballet Theatre": "https://www.pbt.org",
  "Texture Contemporary Ballet": "https://www.textureballet.org",
  "Pittsburgh Savoyards": "https://www.pittsburghsavoyards.org",
  "August Wilson African American Cultural Center": "https://awaacc.org",
  "Pittsburgh Steelers": "https://www.steelers.com",
  "Pittsburgh Penguins": "https://www.nhl.com/penguins",
  "Wilkes-Barre/Scranton Penguins": "https://www.wbspenguins.com",
  "Pittsburgh Pirates": "https://www.mlb.com/pirates",
  "Pittsburgh Passion": "https://www.pittsburghpassion.com",
  "Pittsburgh Thunderbirds": "https://pghthunderbirds.com",
  "Acrisure Stadium": "https://acrisurestadium.com",
  "PPG Paints Arena": "https://www.ppgpaintsarena.com",
  "Stage AE": "https://stageae.com",
  "Petersen Events Center": "https://www.peterseneventscenter.com",
  "Roxian Theatre": "https://www.livenation.com",
  "Carnegie of Homestead Music Hall": "https://librarymusichall.com",
  "Arcade Comedy Theater": "https://www.arcadecomedytheater.com",
  "Pittsburgh Improv": "https://improv.com/pittsburgh",
  "Carnegie Mellon University": "https://www.cmu.edu",
  "University of Pittsburgh": "https://www.pitt.edu",
  "Pittsburgh Panthers": "https://pittsburghpanthers.com",
  "Duquesne University Athletics": "https://goduquesne.com",
  "Robert Morris University Athletics": "https://rmucolonials.com",
  "Visit Pittsburgh": "https://www.visitpittsburgh.com",
  "NFL Draft": "https://www.nfl.com/draft",
  "Phipps Conservatory": "https://www.phipps.conservatory.org",
  "Kennywood": "https://www.kennywood.com",
  "Pittsburgh Vintage Grand Prix": "https://www.pvgp.org",
  "Pittsburgh Irish Festival": "https://pghirishfest.org",
  "Picklesburgh": "https://www.picklesburgh.com",
  "The Great Race": "https://www.rungreatrace.com",
  "Duquesne Incline": "https://duquesneincline.org",
  "Strip District Terminal": "https://stripdistrictterminal.com",
  "GuideStar": "https://www.guidestar.org"}

visited_urls = set()
visited_lock = threading.Lock()
thread_local = threading.local()

def get_playwright_context():
    if not hasattr(thread_local, "playwright"):
        thread_local.playwright = sync_playwright().start()
        thread_local.browser = thread_local.playwright.chromium.launch(headless=True)
        thread_local.context = thread_local.browser.new_context()
    return thread_local.context

def fetch_html(url: str) -> str:
    context = get_playwright_context()
    page = context.new_page()
    try:
        response = page.goto(url, timeout=15000, wait_until="domcontentloaded")
        if response and not response.ok:
            logger.warning(f"HTTP Error {response.status} for {url}")
            return ""
        return page.content()
    except PlaywrightTimeoutError:
        logger.warning(f"Timeout exploring {url}")
        return ""
    except PlaywrightError as e:
        logger.warning(f"Playwright error exploring {url}: {e}")
        return ""
    except Exception as e:
        logger.warning(f"Unexpected error exploring {url}: {e}")
        return ""
    finally:
        page.close()

def load_previously_scraped_documents(filepaths: List[str]) -> tuple:
    loaded_urls = set()
    loaded_docs = []
    for filepath in filepaths:
        if not os.path.exists(filepath):
            logger.warning(f"File {filepath} not found. Skipping.")
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                documents = json.load(f)
                for doc in documents:
                    if "url" in doc and doc["url"] not in loaded_urls:
                        loaded_urls.add(doc["url"])
                        loaded_docs.append(doc)
            logger.info(f"Loaded {len(documents)} documents from {filepath}")
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
    return loaded_urls, loaded_docs


MIN_TEXT_LENGTH = 100          
MIN_WORD_COUNT = 15            
MAX_BOILERPLATE_RATIO = 0.85  

USELESS_TITLE_KEYWORDS = [
    "404", "page not found", "access denied", "forbidden",
    "login", "sign in", "subscribe", "cookie", "captcha",
    "error", "maintenance", "coming soon", "under construction",
]

USELESS_BODY_KEYWORDS = [
    "enable javascript", "enable cookies", "browser not supported",
    "please verify you are a human", "access to this page has been denied",
    "this site requires javascript",
]


def is_useful_content(doc: Dict) -> bool:
    if not doc or not doc.get("text"):
        return False

    text = doc["text"]
    title = (doc.get("title") or "").lower()

    
    if any(kw in title for kw in USELESS_TITLE_KEYWORDS):
        
        return False

    text_lower = text.lower()
    if any(kw in text_lower for kw in USELESS_BODY_KEYWORDS):
        
        return False
    if len(text) < MIN_TEXT_LENGTH:
        
        return False

    words = text.split()
    if len(words) < MIN_WORD_COUNT:
        
        return False
    lines = [l for l in text.splitlines() if l.strip()]
    if lines:
        boilerplate_lines = sum(1 for l in lines if len(l.split()) <= 3)
        ratio = boilerplate_lines / len(lines)
        if ratio > MAX_BOILERPLATE_RATIO:
            return False

    return True

class WebScraper:
    def __init__(self, urls, max_depth=2, max_workers=4):
        self.urls = urls
        self.max_depth = max_depth
        self.max_workers = max_workers 
        self.documents = []

    def get_subpage_links(self, html: str, base_url: str, same_domain: bool = True) -> List[str]:
        if not html:
            return []
            
        soup = BeautifulSoup(html, "lxml")
        links = []
        base_domain = urlparse(base_url).netloc

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)

            parsed = urlparse(full_url)
            if parsed.scheme not in ("http", "https"):
                continue
            if same_domain and parsed.netloc != base_domain:
                continue

            skip_patterns = [
                "#", "login", "signup", "cart", "search", 
                ".pdf", ".jpg", ".png", ".gif", ".zip",
            ]
            if any(pat in full_url.lower() for pat in skip_patterns):
                continue

            links.append(full_url)
        return list(set(links))

    def _fetch_and_get_links(self, url: str) -> List[str]:
        time.sleep(0.5) 
        html = fetch_html(url)
        return self.get_subpage_links(html, url)

    def explore(self, urls, depth=0):
        if depth >= self.max_depth:
            return []
            
        urls_to_visit = []
        with visited_lock:
            for url in urls:
                if url not in visited_urls:
                    visited_urls.add(url)
                    urls_to_visit.append(url)
                    
        if not urls_to_visit:
            return []

        all_links = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self._fetch_and_get_links, url): url for url in urls_to_visit}
            for future in concurrent.futures.as_completed(future_to_url):
                discovered_links = future.result()
                if discovered_links:
                    all_links.extend(discovered_links)

        all_links.extend(self.explore(list(set(all_links)), depth + 1))
        return list(set(all_links))

    def _scrape_url(self, url: str) -> Dict:
        time.sleep(0.5)
        html = fetch_html(url)
        if not html:
            return None
            
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            main_content = soup.find("main") or soup.find("article") or soup.find("body")
            if main_content is None:
                main_content = soup

            text = main_content.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = "\n".join(lines)
            
            doc = {"id": title, "url": url, "text": text}
            if not is_useful_content(doc):
                logger.info(f"Filtered out (not useful): {title or url}")
                return None
            logger.info(f"Successfully scraped: {title or url}")
            return doc
            
        except Exception as e:
            logger.warning(f"Error parsing {url}: {e}")
            return None

    def scrape(self):

        discovered_urls = self.explore(list(self.urls.values()))
        
        urls_to_scrape = list(set(self.urls.values()).union(set(discovered_urls)))

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self._scrape_url, url): url for url in urls_to_scrape}
            for future in concurrent.futures.as_completed(future_to_url):
                doc = future.result()
                if doc:
                    self.documents.append(doc)

def save_documents(documents: List[Dict], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(documents)} documents to {output_path}")

if __name__ == "__main__":

    previous_files = [
        "output/scraped_documents_3.json"
    ]
    previous_urls, previous_docs = load_previously_scraped_documents(previous_files)

    with visited_lock:
        visited_urls.update(previous_urls)

    scraper = WebScraper(SCRAPE_URLS_7, max_depth=1, max_workers=4)
    scraper.scrape()

    target_urls = set(scraper.urls.values())
    reused = 0
    for doc in previous_docs:
        if doc["url"] in target_urls and is_useful_content(doc):
            scraper.documents.append(doc)
            reused += 1

    save_documents(scraper.documents, "output/scraped_documents_9.json")

    # scraper = WebScraper(SCRAPE_URLS_4, max_depth=2, max_workers=4)
    # scraper.scrape()
    # save_documents(scraper.documents, "output/scraped_documents_4.json")

    # scraper = WebScraper(SCRAPE_URLS_5, max_depth=0, max_workers=4)
    # scraper.scrape()
    # save_documents(scraper.documents, "output/scraped_documents_5.json")