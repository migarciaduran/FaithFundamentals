#!/usr/bin/env python3
"""
OneDrive Folder Downloader - Simplified and Robust Version
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Configuration
DOWNLOAD_DIR = "/Users/miguelgarcia/Desktop/FOF/Downloads"

# OneDrive folder URLs - using your exact links
FOLDERS = {
    "FoF_Class_Materials": "https://onedrive.live.com/?redeem=aHR0cHM6Ly8xZHJ2Lm1zL2YvYy9lNDU5YjRmYTEyODQ4NmUwL0V1bVR0WWh3Tm14S2hHUjRTSTFQdWVjQnJOS19GZDNFZnM5U0VpbnZzZFEyOUE%5FZT01Om5rMDNHRiZzaGFyaW5ndjI9dHJ1ZSZmcm9tU2hhcmU9dHJ1ZSZhdD05&id=E459B4FA128486E0%21sdab7b59d7f674f33a193daf4c786b36e&cid=E459B4FA128486E0&sb=name&sd=1",
    "FoF_Lessons": "https://onedrive.live.com/?redeem=aHR0cHM6Ly8xZHJ2Lm1zL2YvYy9lNDU5YjRmYTEyODQ4NmUwL0V1bVR0WWh3Tm14S2hHUjRTSTFQdWVjQnJOS19GZDNFZnM5U0VpbnZzZFEyOUE%5FZT01Om5rMDNHRiZzaGFyaW5ndjI9dHJ1ZSZmcm9tU2hhcmU9dHJ1ZSZhdD05&id=E459B4FA128486E0%21s7f1f54ecb8824576a59fb3e66bd4b83e&cid=E459B4FA128486E0&sb=name&sd=1"
}


def setup_driver(download_folder):
    """Configure Chrome driver with download settings."""
    os.makedirs(download_folder, exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver


def wait_for_downloads(download_folder, timeout=30):
    """Wait for all downloads to complete."""
    end_time = time.time() + timeout
    while time.time() < end_time:
        downloading = [f for f in os.listdir(download_folder) if f.endswith('.crdownload')]
        if not downloading:
            return True
        time.sleep(0.5)
    return False


def download_files_from_folder(driver, folder_url, folder_name, download_base):
    """Download all files from a OneDrive folder."""
    download_folder = os.path.join(download_base, folder_name)
    os.makedirs(download_folder, exist_ok=True)
    
    # Set download directory
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_folder
    })
    
    print(f"\n📂 Processing folder: {folder_name}")
    print(f"   Download to: {download_folder}")
    
    # Check existing files
    existing_files = set(os.listdir(download_folder)) if os.path.exists(download_folder) else set()
    print(f"   Already have {len(existing_files)} files")
    
    driver.get(folder_url)
    time.sleep(5)
    
    try:
        # Wait for file list
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[role='row']"))
        )
        time.sleep(2)
        
        # Download files as we scroll through them
        print("   🔄 Scrolling and downloading files...")
        downloaded_files = set()  # Track what we've already processed
        downloaded_count = 0
        skipped_count = 0
        
        # Click on first item to focus the list
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "[role='row'][aria-rowindex]")
            if rows:
                rows[0].click()
                time.sleep(0.3)
        except:
            pass
        
        # Scroll through entire list with arrow keys
        same_files_count = 0
        last_files_seen = set()
        
        for i in range(200):  # Max iterations
            # Get all visible files
            rows = driver.find_elements(By.CSS_SELECTOR, "[role='row'][aria-rowindex]")
            current_files = set()
            
            for row in rows:
                try:
                    btn = row.find_element(By.CSS_SELECTOR, "button[data-automationid='FieldRenderer-name']")
                    name = btn.text.strip()
                    if name:
                        current_files.add(name)
                        
                        # Skip if already processed
                        if name in downloaded_files:
                            continue
                        
                        downloaded_files.add(name)
                        
                        # Skip if already exists on disk
                        if name in existing_files:
                            print(f"   ⏭️  Skip (exists): {name}")
                            skipped_count += 1
                            continue
                        
                        # Download this file
                        print(f"   📥 Downloading: {name}")
                        try:
                            # Scroll element into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                            time.sleep(0.2)
                            
                            # Right-click for context menu
                            ActionChains(driver).context_click(btn).perform()
                            time.sleep(0.8)
                            
                            # Click Download
                            dl_btn = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(@name,'Download') or .//span[text()='Download']]"))
                            )
                            dl_btn.click()
                            time.sleep(1.5)
                            
                            # Wait for download
                            wait_for_downloads(download_folder, timeout=30)
                            downloaded_count += 1
                            print(f"      ✅ Downloaded!")
                            
                        except Exception as e:
                            print(f"      ⚠️  Error: {e}")
                        
                        # Close any menu
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(0.3)
                        
                except:
                    pass
            
            # Check if we've reached the end (no new files)
            if current_files == last_files_seen:
                same_files_count += 1
                if same_files_count >= 15:
                    break
            else:
                same_files_count = 0
                last_files_seen = current_files
            
            # Press down arrow to scroll
            ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
            time.sleep(0.15)
        
        print(f"\n   ✅ Done! Downloaded {downloaded_count} new files, skipped {skipped_count} existing")
        print(f"   📊 Total files processed: {len(downloaded_files)}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("=" * 60)
    print("OneDrive Folder Downloader")
    print("=" * 60)
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    print("\n🚀 Starting Chrome browser...")
    driver = setup_driver(DOWNLOAD_DIR)
    
    try:
        for folder_name, folder_url in FOLDERS.items():
            download_files_from_folder(driver, folder_url, folder_name, DOWNLOAD_DIR)
            time.sleep(2)
        
        print("\n" + "=" * 60)
        print("✅ All done!")
        print(f"📁 Files saved to: {DOWNLOAD_DIR}")
        print("=" * 60)
        
    finally:
        print("\n🔒 Closing browser...")
        driver.quit()


if __name__ == "__main__":
    main()
