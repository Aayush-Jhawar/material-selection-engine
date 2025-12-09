import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import time
import random
import os
from bs4 import BeautifulSoup
import re

# Configuration
BASE_URL = "https://www.matweb.com"
GUIDS_FILE = 'matweb_guids_checkpoint.csv'
OUTPUT_FILE = 'comprehensive_matweb_data.csv'

# Optimized settings for safe, fast scraping on a clean IP
MAX_CONCURRENT_SCRAPERS = 3 
SCRAPING_DELAY_RANGE = (10, 15) # 10-15 seconds delay per request
MAX_RETRIES = 3 
RETRY_PAUSE_SECONDS = 300       # 5 minutes pause on hard error (timeout/server issue)

# Extraction Helper Functions

def clean_value(text):
    if text:
        # Use get_text(strip=True) for initial cleanup
        text = text.get_text(strip=True) if hasattr(text, 'get_text') else text.strip()
        # Clean common extraneous characters
        text = text.replace('\xa0', ' ').replace('\t', '').replace('\n', ' ')
        
        # Simple cleanup to remove unit converter links/symbols
        text = re.sub(r'(\d|\s)\s*µ(m|in)/\w+', r'\1', text) 
        return text.strip()
    return ''

def extract_material_properties(html_content, guid):
    material_info = {'GUID': guid}
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Descriptive Fields
    try:
        title_text = soup.find('title').text.strip().replace('\t', '')
        material_info['Material Name'] = title_text.split(',')[0].strip()
        
        category_row = soup.find('tr', id=re.compile(r'trMatlGroups'))
        material_info['Categories'] = clean_value(category_row.find('td')) if category_row else 'N/A'
        
        notes_row = soup.find('tr', id=re.compile(r'trMatlNotes'))
        material_info['Material Notes'] = clean_value(notes_row.find('td')) if notes_row else 'N/A'
    except:
        pass 

    # 2. Quantitative Property Extraction
    data_container = soup.find('div', id=re.compile(r'pnlMaterialData'))
    
    if data_container:
        property_tables = data_container.find_all('table')
        current_category = None
        
        for table in property_tables:
            category_header = table.find('th', attrs={'colspan': ['4', '6']})
            if not category_header:
                category_header = table.find('th', attrs={'scope': 'col', 'colspan': '6', 'align': 'left'})
            
            if category_header and category_header.text.strip():
                current_category = clean_value(category_header)
                if current_category == "Descriptive Properties":
                    pass
                
            # Iterate over rows for properties
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                
                if current_category:
                    
                    if len(cells) >= 4 and current_category != "Descriptive Properties":                        
                        prop_name = clean_value(cells[0])
                        metric_cell = cells[1]
                        comment_cell = cells[3]
                        
                        metric_value = clean_value(metric_cell)
                        comment = clean_value(comment_cell)
                        
                        key = f"{current_category} - {prop_name} [Metric]"
                        
                        if prop_name and metric_value and len(prop_name) > 3:
                            material_info[key] = metric_value
                            
                            # Capture conditional data
                            condition_text = metric_cell.find('span', class_='dataCondition')
                            if condition_text:
                                condition = condition_text.get_text(strip=True).replace('\n', ' ').strip()
                                if condition and '@' in condition:
                                    material_info[f"{key} (Condition)"] = condition
                            
                            if comment:
                                material_info[f"{key} (Comment)"] = comment

                    elif current_category == "Descriptive Properties" and len(cells) >= 3:
                        # Descriptive Row: [Prop_Name, Value, Comment]
                        prop_name = clean_value(cells[0])
                        value = clean_value(cells[1])
                        comment = clean_value(cells[2])
                        
                        if prop_name and value and len(prop_name) > 3:
                            material_info[f"{current_category} - {prop_name}"] = value
                            if comment:
                                material_info[f"{current_category} - {prop_name} (Comment)"] = comment
                        
    return material_info

def save_to_checkpoint(data_list):
    if not data_list:
        return
        
    current_df = pd.DataFrame(data_list)
    write_header = not os.path.exists(OUTPUT_FILE)
    current_df.to_csv(OUTPUT_FILE, mode='a', header=write_header, index=False)

# Main Scraper Logic

async def scrape_single_material_concurrent(browser, guid_index, guid, total_guids):   
    page = await browser.new_page()
    material_url = f"{BASE_URL}/search/DataSheet.aspx?MatGUID={guid}"
    
    for attempt in range(1, MAX_RETRIES + 1):
        wait_time = random.uniform(*SCRAPING_DELAY_RANGE)
        print(f"[{guid_index+1}/{total_guids}] Waiting {wait_time:.2f}s...")
        await asyncio.sleep(wait_time) 

        try:
            # Navigate and Wait for load
            await page.goto(material_url, wait_until="networkidle", timeout=30000)
            
            content = await page.content()
            if "Your IP Address has been restricted" in content:
                print(f"!!! IP RESTRICTED. Halting this job. !!!")
                return {'status': 'IP_BANNED'}
            
            # Success: Extract data
            material_info = extract_material_properties(content, str(guid))
            print(f"SUCCESS (Attempt {attempt}): {material_info.get('Material Name', 'N/A')}")
            await page.close() 
            return material_info
            
        except Exception as e:
            print(f"ERROR: {e}. Attempt {attempt} failed. Pausing thread for {RETRY_PAUSE_SECONDS}s...")
            await asyncio.sleep(RETRY_PAUSE_SECONDS) 
            continue 
            
    await page.close() 
    print(f"FAILED: Max retries ({MAX_RETRIES}) reached for {guid}.")
    return {'status': 'MAX_RETRIES_FAILED'}


async def playwright_scraper_manager():
    if not os.path.exists(GUIDS_FILE):
        print(f"Error: GUID checkpoint file not found at {GUIDS_FILE}.")
        return

    guids_df = pd.read_csv(GUIDS_FILE)
    all_guids = guids_df['GUID'].astype(str).tolist()
    total_guids = len(all_guids)
    
    # Initial setup and resume logic
    scraped_guids = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_csv(OUTPUT_FILE, usecols=['GUID'])
            scraped_guids = set(existing_df['GUID'].astype(str).tolist())
        except Exception:
            pass

    jobs = []
    for i, guid in enumerate(all_guids):
        if guid not in scraped_guids:
            jobs.append((i, guid))
    
    
    random.shuffle(jobs)
    total_jobs = len(jobs)
    
    
    print("Initializing Full Phase 2 Run ")
    print(f"Total GUIDs remaining to process: {total_jobs}")
    print(f"Concurrency Level: {MAX_CONCURRENT_SCRAPERS} workers")
    
    checkpoint_list = []

    async with async_playwright() as p:
        # Launch browser once (headless=True for full run)
        browser = await p.chromium.launch(headless=True) 

        # CRITICAL: Initial Delay
        initial_wait = random.uniform(50, 100) 
        print(f"\n*** CRITICAL: Waiting {initial_wait:.2f}s before starting first request. ***")
        await asyncio.sleep(initial_wait)

        # Create tasks for all jobs
        tasks = []
        for index, guid in jobs:
            tasks.append(scrape_single_material_concurrent(browser, index, guid, total_guids))
        
        # Concurrently execute tasks, respecting MAX_CONCURRENT_SCRAPERS
        for i in range(0, len(tasks), MAX_CONCURRENT_SCRAPERS):
            batch = tasks[i:i + MAX_CONCURRENT_SCRAPERS]
            results = await asyncio.gather(*batch)
            
            for result in results:
                status = result.get('status')
                
                if status == 'IP_BANNED':
                    print("\nIMMEDIATE STOP: IP BAN DETECTED. Shutting down browser.")
                    await browser.close()
                    save_to_checkpoint(checkpoint_list)
                    return 
                
                elif status is None:
                    checkpoint_list.append(result)
                    
                    # Checkpoint Logic (Save every 50 records)
                    if len(checkpoint_list) >= 50:
                        print(f"\nCHECKPOINT: Saving 50 records to CSV")
                        save_to_checkpoint(checkpoint_list)
                        checkpoint_list = []

        await browser.close()

    # Final save
    if checkpoint_list:
        print("\nFINAL CHECKPOINT: Saving remaining records")
        save_to_checkpoint(checkpoint_list)
        
    final_scraped_count = len(pd.read_csv(OUTPUT_FILE)) if os.path.exists(OUTPUT_FILE) else 0
    print("\n" + "="*50)
    print(f"PHASE 2 SCRAPE COMPLETE. Total UNIQUE records saved: {final_scraped_count}")
    print("="*50)

# Execution
if __name__ == "__main__":
    asyncio.run(playwright_scraper_manager())