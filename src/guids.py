import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}
BASE_URL = "https://www.matweb.com"
SEARCH_URL = 'https://www.matweb.com/search/QuickText.aspx'
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

MAX_WORKERS = 4
SEARCH_SEGMENTS = [chr(i) for i in range(ord('a'), ord('z') + 1)] + [str(i) for i in range(10)]
GUIDS_FILE = 'matweb_guids_checkpoint.csv'


def extract_asp_net_state(soup):
    view_state_tag = soup.find('input', {'name': '__VIEWSTATE'})
    view_state_gen_tag = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
    
    view_state = view_state_tag['value'] if view_state_tag else None
    view_state_gen = view_state_gen_tag['value'] if view_state_gen_tag else None
    
    if not view_state or not view_state_gen:
        if "Your IP Address has been restricted" in str(soup):
            raise ConnectionRefusedError("IP Blocked by MatWeb.")
        raise ValueError("Could not find required ASP.NET state fields.") 
        
    return view_state, view_state_gen

def build_next_page_payload(view_state, view_state_gen, page_number, search_term):
    
    payload = {
        '__EVENTTARGET': 'ctl00$ContentMain$ucSearchResults1$lnkNextPage',
        '__EVENTARGUMENT': '',
        '__LASTFOCUS': '',
        '__VIEWSTATE': view_state,
        '__VIEWSTATEGENERATOR': view_state_gen,
        
        # Essential fields to maintain the search state
        'ctl00$txtQuickText': search_term, # Use the current search segment
        'ctl00$ContentMain$ucSearchResults1$drpPageSize1': '200', # Keep results high
        'ctl00$ContentMain$ucSearchResults1$drpPageSelect1': str(page_number), 
        'ctl00$ContentMain$ucSearchResults1$drpFolderList': '0',
        'ctl00$ContentMain$ucSearchResults1$txtFolderMatCount': '0/0',
    }
    return payload


def scrape_guids_via_segment(search_term):
    all_guids = set()
    page = 1
    
    initial_delay = random.uniform(0, 10)
    print(f"[THREAD-{search_term.upper()}] Initializing. Waiting {initial_delay:.2f}s before GET...")
    time.sleep(initial_delay)
    
    initial_search_url = f"{SEARCH_URL}?SearchText={search_term}"
    print(f"[THREAD-{search_term.upper()}] Step 1: Submitting initial GET search...")
    
    try:
        response = SESSION.get(initial_search_url, timeout=15)
        response.raise_for_status()
        current_soup = BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"[THREAD-{search_term.upper()}] Error submitting initial GET: {e}. Stopping segment.")
        return all_guids # Return empty set if initial search fails

    # --- Step 2: Loop through pages using subsequent POSTs ---
    while True:
        print(f"[THREAD-{search_term.upper()}] Scraping page {page}")

        # Extract GUIDs from the current page
        for link in current_soup.find_all('a', href=True):
            href = link.get('href')
            if 'bassnum=' in href:
                guid = href.split('bassnum=')[-1].split('&')[0]
                all_guids.add(guid)
            elif 'MatGUID=' in href:
                guid = href.split('MatGUID=')[-1].split('&')[0]
                all_guids.add(guid)
        
        # Check for stop condition and prepare for next POST
        try:
            next_link_tag = current_soup.find('a', id='ctl00_ContentMain_ucSearchResults1_lnkNextPage')
            if not next_link_tag:
                print(f"[THREAD-{search_term.upper()}] Last page reached. Stopping segment.")
                break
            
            view_state, view_state_gen = extract_asp_net_state(current_soup)
            
        except ConnectionRefusedError:
            print(f"[THREAD-{search_term.upper()}] !!! IP Block Detected. Halting thread !!!")
            break
        except Exception as e:
            print(f"[THREAD-{search_term.upper()}] Failed to extract state: {e}. Halting thread.")
            break
            
        # --- Step 3: Prepare and send the 'Next Page' POST request ---
        payload = build_next_page_payload(view_state, view_state_gen, page, search_term)
        page += 1 

        # MANDATORY DELAY for navigation (Phase 1: Moderate Speed)
        wait_time = random.uniform(3, 7)
        print(f"[THREAD-{search_term.upper()}] POSTing for page {page}. Waiting {wait_time:.2f}s...")
        time.sleep(wait_time) 

        try:
            post_response = SESSION.post(SEARCH_URL, data=payload, timeout=20)
            post_response.raise_for_status()
            current_soup = BeautifulSoup(post_response.content, 'html.parser')
            
        except requests.exceptions.RequestException as e:
            print(f"[THREAD-{search_term.upper()}] POST Error: {e}. Stopping segment.")
            break
            
    print(f"[THREAD-{search_term.upper()}] Finished. GUIDs collected: {len(all_guids)}")
    return all_guids

# --- Main Concurrent Execution ---

def concurrent_guid_collector():
    """Manages the ThreadPoolExecutor to run searches concurrently."""
    final_guids = set()
    
    print("="*50)
    print(f"Starting concurrent GUID collection with {MAX_WORKERS} workers...")
    print(f"Total Segments to search: {len(SEARCH_SEGMENTS)}")
    print("="*50)
    
    # Use ThreadPoolExecutor to manage parallel scraping
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        # Map the scraping function to all search segments
        # executor.map returns results in the order the calls were made
        future_to_segment = {executor.submit(scrape_guids_via_segment, segment): segment for segment in SEARCH_SEGMENTS}
        
        # Collect results from all threads as they complete
        for future in future_to_segment:
            segment = future_to_segment[future]
            try:
                guid_set = future.result()
                if guid_set:
                    final_guids.update(guid_set)
                    print(f"*** Segment {segment.upper()} complete. Total GUIDs now: {len(final_guids)}")
            except Exception as exc:
                print(f"Segment {segment.upper()} generated an exception: {exc}")

    # Save final checkpoint
    pd.Series(list(final_guids)).to_csv(GUIDS_FILE, index=False, header=['GUID'])
    print("\n" + "="*50)
    print(f"CONCURRENT COLLECTION COMPLETE. Total UNIQUE GUIDs saved: {len(final_guids)}")
    print("Next: Use this list for the slow, detailed data scrape (Phase 2).")
    print("="*50)
    
    return list(final_guids)

# --- Execution ---
if __name__ == "__main__":
    concurrent_guid_collector()