import argparse
import csv
import json
import logging
import os
import random
import time
from datetime import datetime
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("linkedin_jobs_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInJobScraper:
    def __init__(self, headless=True, username=None):
        """
        Initialize the LinkedIn Job Scraper.
        
        Args:
            headless (bool): Whether to run Chrome in headless mode.
            username (str): Your username for attribution.
        """
        self.username = username
        self.headless = headless  # Store headless state
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        if self.headless:  # Use self.headless
            chrome_options.add_argument("--headless=new")  # Updated headless syntax
            
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Rotate user agents to avoid detection
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15"
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        try:
            # Direct initialization of Chrome webdriver
            logger.info("Initializing Chrome WebDriver")
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            print("\nERROR: Could not initialize Chrome WebDriver.")
            print("\nPlease make sure Chrome is installed and chromedriver is properly set up:")
            print("  1. Install Chrome browser if not already installed")
            print("  2. Install chromedriver using Homebrew:")
            print("     brew install --cask chromedriver")
            print("  3. Allow chromedriver to run by executing:")
            print("     xattr -d com.apple.quarantine $(which chromedriver)")
            raise
    
    def construct_url(self, job_title, location):
        """
        Construct URL for LinkedIn jobs search with the given parameters.
        
        Args:
            job_title (str): The job title to search for.
            location (str): The location to search for jobs in.
            
        Returns:
            str: The constructed URL.
        """
        # Encode the search parameters for the URL
        encoded_job = quote(job_title)
        encoded_location = quote(location)
        
        # LinkedIn search URL
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_job}&location={encoded_location}"
        
        logger.info(f"Constructed URL: {search_url}")
        return search_url
    
    def navigate_to_search_results(self, job_title, location):
        """
        Navigate to the job search results page.
        
        Args:
            job_title (str): The job title to search for.
            location (str): The location to search in.
            
        Returns:
            bool: True if navigation was successful, False otherwise.
        """
        try:
            url = self.construct_url(job_title, location)
            self.driver.get(url)
            
            # Wait for the page and job list to load - reduced timeout
            WebDriverWait(self.driver, 10).until(  # Reduced from 20 seconds
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
            )
            
            # Handle cookie consent if present
            try:
                cookie_button = WebDriverWait(self.driver, 3).until(  # Reduced from 5 seconds
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-global-alert__dismiss"))
                )
                cookie_button.click()
                logger.info("Closed cookie consent dialog")
            except:
                logger.info("No cookie consent dialog found or already closed")
            
            # Add a check for list visibility and potential delay for manual sign-in
            try:
                # Verify the job list is actually visible after potential overlays/sign-in prompts
                WebDriverWait(self.driver, 5).until(  # Reduced from 10 seconds
                    EC.visibility_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
                )
                logger.info("Job results list is visible.")

                # Optional delay for manual intervention (e.g., sign-in) if not headless
                if not self.headless:
                    manual_wait_time = 7  # Reduced from 15 seconds
                    logger.info(f"Running in non-headless mode. Pausing for {manual_wait_time} seconds for potential manual sign-in...")
                    time.sleep(manual_wait_time)
                    logger.info("Resuming script.")

            except Exception as e:
                logger.warning(f"Job results list not found or not visible after initial load. A sign-in might be required or the page structure could have changed: {e}")
                self.driver.save_screenshot("debug_list_not_visible.png")
                logger.info("Saved screenshot: debug_list_not_visible.png")
                # Return False as we cannot proceed without the job list
                return False
            
            # Take a screenshot for debugging after potential waits
            self.driver.save_screenshot("search_results_ready.png")
            logger.info(f"Screenshot saved as search_results_ready.png")
            
            logger.info(f"Successfully navigated to search results for {job_title} in {location}")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to search results: {e}")
            self.driver.save_screenshot("error_navigation.png")
            logger.info(f"Error screenshot saved as error_navigation.png")
            return False
    
    def scroll_and_collect_jobs(self, max_jobs=50, max_scrolls=20):
        """
        Scroll through job listings and collect data.
        
        Args:
            max_jobs (int): Maximum number of job listings to collect.
            max_scrolls (int): Maximum number of scrolls to perform.
            
        Returns:
            list: List of dictionaries containing job data.
        """
        jobs_data = []
        processed_job_ids = set() # Keep track of processed job IDs to avoid duplicates
        scrolls = 0
        last_job_count = 0

        logger.info(f"Starting to collect up to {max_jobs} job listings...")

        try:
            # LinkedIn sıklıkla yapısını değiştirir, bu yüzden birkaç farklı seçiciyi deneyeceğiz
            job_list_container_selector = (By.CSS_SELECTOR, ".jobs-search__results-list, ul.scaffold-layout__list-container")
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(job_list_container_selector)
            )
            job_list = self.driver.find_element(*job_list_container_selector)

            # Sayfanın yüklenmesi için kısa süre bekle
            time.sleep(0.5)  

            # TEMELDEKİ SORUN: LinkedIn'de iş detayları paneline tıklamak yerine,
            # doğrudan kartlardan bilgileri çekmek daha hızlı ve güvenilir olacak

            while len(jobs_data) < max_jobs and scrolls < max_scrolls:
                # İş kartlarını bulmak için daha genel seçiciler
                job_card_selectors = [
                    "div.base-card", # Ekran görüntüsünde görülen format
                    "div.job-search-card",
                    "li.jobs-search-results__list-item", 
                    "div.jobs-search-result-item",
                    "div[data-job-id]",
                    ".job-card-container"
                ]
                
                found_cards = False
                job_cards = []
                
                # Farklı seçicileri deneyelim
                for selector in job_card_selectors:
                    try:
                        job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if job_cards:
                            logger.info(f"Found {len(job_cards)} job cards using selector: '{selector}'")
                            found_cards = True
                            break
                    except Exception:
                        continue
                
                if not found_cards:
                    logger.warning("Could not find job cards with any selector after scroll. Trying to scroll more.")
                    self.driver.execute_script("window.scrollBy(0, 500);")  # Az miktarda scroll yapalım
                    time.sleep(0.5)
                    scrolls += 1
                    if scrolls >= 5 and len(jobs_data) == 0:
                        logger.warning("Multiple scrolls but still no jobs found. Page structure might have changed.")
                        # Ekran görüntüsü alalım ve HTML'i loglayelım
                        self.driver.save_screenshot(f"debug_page_structure_{scrolls}.png")
                        continue

                # ÖNEMLİ DEĞİŞİKLİK: Detay paneli beklemeden, doğrudan kartlardan bilgileri çekelim
                new_jobs_found_this_iteration = 0
                for i, job_card in enumerate(job_cards):
                    # En fazla max_jobs kadar kartı işleyelim
                    if len(jobs_data) >= max_jobs:
                        break
                        
                    # Gereksiz kartları atlayalım
                    if i >= max_jobs * 2:  # Çalışma alanını sınırlayalım
                        break
                        
                    try:
                        # Kartı görünür hale getirelim
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'auto'});", job_card)
                        time.sleep(0.1)
                        
                        # Karttan doğrudan bilgileri çekelim - DETAY PANELİNE TIKLAMA OLMADAN!
                        job_data = self.get_job_details_from_card(job_card)
                        
                        if job_data:
                            job_id = job_data["id"]
                            if job_id not in processed_job_ids:
                                jobs_data.append(job_data)
                                processed_job_ids.add(job_id)
                                new_jobs_found_this_iteration += 1
                                logger.info(f"Collected job {len(jobs_data)}/{max_jobs}: {job_data.get('title', 'Unknown title')}")
                    except Exception as e:
                        logger.warning(f"Error processing job card {i}: {str(e)[:100]}...")
                
                # Maksimum iş sayısına ulaştıysak döngüden çıkalım
                if len(jobs_data) >= max_jobs:
                    logger.info(f"Reached max jobs limit: {max_jobs}")
                    break
                
                # Yeni iş bulamadıysak ve yeterince scroll yaptıysak sonlandıralım
                if new_jobs_found_this_iteration == 0 and scrolls > 5:
                    logger.info("No new jobs found after several scrolls. Stopping.")
                    break
                
                # Sayfayı aşağı kaydıralım
                self.driver.execute_script("window.scrollBy(0, 800);")  # Daha az scroll yap
                scrolls += 1
                time.sleep(0.5)  # Kısa bekleme ile scroll
                
                # Toplanan iş sayısı artmıyorsa bir süre sonra sonlandıralım
                if scrolls > 3 and len(jobs_data) == last_job_count:
                    logger.info("Job count hasn't increased for several scrolls. Stopping.")
                    break
                
                last_job_count = len(jobs_data)
            
            logger.info(f"Finished collecting. Collected {len(jobs_data)} job listings after {scrolls} scrolls.")
            return jobs_data
            
        except Exception as e:
            logger.error(f"Error during job collection: {e}")
            self.driver.save_screenshot("error_during_collection.png")
            return jobs_data

    def extract_job_data_improved(self):
        """
        LinkedIn'in güncel yapısına göre optimize edilmiş iş detayları çekme fonksiyonu
        """
        try:
            # Detay paneli yerine doğrudan tıklanabilir karttan bilgileri almayı deneyelim
            # LinkedIn'in yeni yapısında detay panelini beklemek yerine, sayfadaki bilgileri doğrudan çekelim
            
            # İş ID'sini URL'den alalım
            job_id = None
            job_link = self.driver.current_url
            try:
                if "currentJobId=" in job_link:
                    job_id = job_link.split("currentJobId=")[1].split("&")[0]
                elif "/jobs/view/" in job_link:
                    job_id = job_link.split("/jobs/view/")[1].split("/")[0].split("?")[0]
                else:
                    job_id = f"linkedin_job_{int(time.time())}"
            except:
                job_id = f"linkedin_job_{int(time.time())}"
            
            # Bekleme sürelerini kısaltalım ve yalnızca temel bilgileri almaya çalışalım
            # Detay panelini beklemek yerine tıklanan kartın içeriğini doğrudan almayı deneyelim

            # İş başlığı için seçiciler
            title_selectors = [
                ".jobs-unified-top-card__job-title", 
                ".job-details-jobs-unified-top-card__job-title",
                ".artdeco-entity-lockup__title",
                ".job-card-list__title",
                ".base-search-card__title"
            ]
            
            title = "Unknown Title"
            for selector in title_selectors:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    continue
            
            # Eğer detay panelinde başlık bulunamadıysa, tarayıcı sayfasındaki bilgileri almaya çalışalım
            if title == "Unknown Title":
                try:
                    # Sayfa başlığından bilgi alalım (genellikle "İş Başlığı | Şirket Adı | LinkedIn" formatındadır)
                    page_title = self.driver.title
                    if " | " in page_title:
                        title = page_title.split(" | ")[0].strip()
                except:
                    pass
            
            # Şirket adı seçicileri
            company_selectors = [
                ".jobs-unified-top-card__company-name",
                ".jobs-unified-top-card__subtitle-primary-grouping a",
                ".artdeco-entity-lockup__subtitle",
                ".base-search-card__subtitle"
            ]
            
            company = "Unknown Company"
            for selector in company_selectors:
                try:
                    company_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    company = company_elem.text.strip()
                    if company:
                        break
                except:
                    continue
            
            # Eğer detay panelinde şirket adı bulunamadıysa, sayfa başlığından almayı deneyelim
            if company == "Unknown Company":
                try:
                    page_title = self.driver.title
                    if " | " in page_title and len(page_title.split(" | ")) > 1:
                        company = page_title.split(" | ")[1].strip()
                except:
                    pass
            
            # Konum seçicileri
            location_selectors = [
                ".jobs-unified-top-card__bullet",
                ".jobs-unified-top-card__location",
                ".artdeco-entity-lockup__caption"
            ]
            
            location = "Unknown Location"
            for selector in location_selectors:
                try:
                    location_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    location = location_elem.text.strip()
                    if location:
                        break
                except:
                    continue
            
            # İş tanımı seçicileri - bazen yüklenmez, önemli değil
            description = "No description available"
            description_selectors = [
                ".jobs-description-content__text",
                ".jobs-box__html-content",
                ".jobs-description"
            ]
            
            for selector in description_selectors:
                try:
                    description_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    description = description_elem.text.strip()
                    if description:
                        break
                except:
                    continue
            
            # İş ilanı verisini döndürelim - en azından temel bilgileri içersin
            job_data = {
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "job_type": "Not specified", # Detaylı bilgileri pas geçiyoruz
                "description": description[:500] + "..." if len(description) > 500 else description,
                "apply_link": job_link,
                "date_posted": "Unknown date", # Detaylı bilgileri pas geçiyoruz
                "scraped_date": datetime.now().isoformat(),
                "source": "LinkedIn Jobs",
                "attribution": f"Collected via LinkedIn Jobs scraper by @{self.username}" if self.username else "Collected via LinkedIn Jobs scraper"
            }
            
            return job_data
            
        except Exception as e:
            logger.warning(f"Error extracting job data: {str(e)[:200]}")
            return None
            
    def get_job_details_from_card(self, job_card):
        """
        İş kartından temel bilgileri çıkar, detay paneline tıklamadan işlemi hızlandır
        """
        try:
            # Benzersiz ID oluştur
            card_id = job_card.get_attribute('data-job-id') or job_card.get_attribute('id') or f"card_{int(time.time())}"
            
            # İş başlığını bul
            title = "Unknown Title"
            try:
                title_elem = job_card.find_element(By.CSS_SELECTOR, "h3, .job-card-list__title, .base-search-card__title")
                title = title_elem.text.strip()
            except:
                pass
                
            # Şirket adını bul
            company = "Unknown Company"
            try:
                company_elem = job_card.find_element(By.CSS_SELECTOR, "h4, .job-card-container__company-name, .base-search-card__subtitle")
                company = company_elem.text.strip()
            except:
                pass
                
            # Konum bilgisini bul
            location = "Unknown Location"
            try:
                location_elem = job_card.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-item, .job-search-card__location")
                location = location_elem.text.strip()
            except:
                pass
                
            # Link URL'sini bul
            apply_link = ""
            try:
                # Kart içindeki ana linki bul
                link_elem = job_card.find_element(By.TAG_NAME, "a")
                apply_link = link_elem.get_attribute("href")
            except:
                apply_link = self.driver.current_url
                
            # Temel iş verilerini döndür
            return {
                "id": card_id,
                "title": title,
                "company": company,
                "location": location,
                "job_type": "Not specified",
                "description": "No description available",
                "apply_link": apply_link,
                "date_posted": "Unknown date",
                "scraped_date": datetime.now().isoformat(),
                "source": "LinkedIn Jobs",
                "attribution": f"Collected via LinkedIn Jobs scraper by @{self.username}" if self.username else "Collected via LinkedIn Jobs scraper"
            }
            
        except Exception as e:
            logger.warning(f"Error extracting data from card: {e}")
            return None
    
    def save_to_json(self, jobs_data, filename=None):
        """
        Save job data to a JSON file.
        
        Args:
            jobs_data (list): List of job data dictionaries.
            filename (str): Optional filename for the output file.
            
        Returns:
            str: Path to the saved file.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linkedin_jobs_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(jobs_data)} jobs to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return None
    
    def save_to_csv(self, jobs_data, filename=None):
        """
        Save job data to a CSV file.
        
        Args:
            jobs_data (list): List of job data dictionaries.
            filename (str): Optional filename for the output file.
            
        Returns:
            str: Path to the saved file.
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linkedin_jobs_{timestamp}.csv"
        
        try:
            # Define CSV headers based on the job data keys
            if jobs_data:
                fieldnames = jobs_data[0].keys()
            else:
                fieldnames = ["id", "title", "company", "location", "job_type",
                             "description", "apply_link", "date_posted", "scraped_date", 
                             "source", "attribution"]
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(jobs_data)
            
            logger.info(f"Successfully saved {len(jobs_data)} jobs to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return None
    
    def close(self):
        """Close the WebDriver."""
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    """Main function to run the LinkedIn job scraper."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape job listings from LinkedIn.')
    parser.add_argument('--job-title', type=str, required=True, help='Job title to search for')
    parser.add_argument('--location', type=str, required=True, help='Location to search in')
    parser.add_argument('--max-jobs', type=int, default=50, help='Maximum number of jobs to collect')
    parser.add_argument('--max-scrolls', type=int, default=20, help='Maximum number of scrolls to perform')
    parser.add_argument('--output-format', type=str, choices=['json', 'csv', 'both'], default='json', 
                        help='Output format for the scraped data')
    parser.add_argument('--output-file', type=str, help='Output filename (without extension)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--username', type=str, help='Your username for attribution')
    parser.add_argument('--skip-details', action='store_true', help='Skip job details panel and collect only basic info from cards')
    
    args = parser.parse_args()
    
    # Create output filename if not provided
    if not args.output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title_slug = args.job_title.lower().replace(' ', '_')
        location_slug = args.location.lower().replace(' ', '_')
        output_file = f"linkedin_jobs_{job_title_slug}_{location_slug}_{timestamp}"
    else:
        output_file = args.output_file
    
    # Initialize the scraper
    scraper = None
    try:
        scraper = LinkedInJobScraper(headless=args.headless, username=args.username)
        
        # Navigate to the search results page
        if not scraper.navigate_to_search_results(args.job_title, args.location):
            logger.error("Failed to navigate to search results. Exiting.")
            return
        
        # Collect job data
        jobs_data = []
        
        # Job details paneli ile ilgili sorunları çözmek için, doğrudan kartlardan bilgileri çekme modunu etkinleştirdik
        if args.skip_details:
            logger.info("FAST MODE: Skipping job details panel and collecting basic info directly from cards.")
            
            # İş kartlarını bulalım
            job_cards = []
            card_selectors = [
                "div.base-card", 
                "div.job-search-card",
                "li.jobs-search-results__list-item",
                ".job-card-container"
            ]
            
            for selector in card_selectors:
                try:
                    job_cards = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_cards:
                        logger.info(f"Found {len(job_cards)} job cards using selector: '{selector}'")
                        break
                except Exception:
                    continue
            
            # Kartları doğrudan işleyelim
            for i, card in enumerate(job_cards):
                if i >= args.max_jobs:
                    break
                    
                try:
                    # Kartı görünür hale getirelim
                    scraper.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'auto'});", card)
                    time.sleep(0.1)
                    
                    # Karttan doğrudan bilgileri çekelim
                    job_data = scraper.get_job_details_from_card(card)
                    if job_data:
                        jobs_data.append(job_data)
                        logger.info(f"Collected job {len(jobs_data)}/{args.max_jobs}: {job_data.get('title', 'Unknown title')}")
                except Exception as e:
                    logger.warning(f"Error processing card {i}: {e}")
                
                # Düzenli olarak scroll yapalım
                if i % 5 == 0 and i > 0:
                    scraper.driver.execute_script("window.scrollBy(0, 300);")
                    time.sleep(0.2)
        else:
            # Normal scroll ve detay paneli modunu kullan
            jobs_data = scraper.scroll_and_collect_jobs(max_jobs=args.max_jobs, max_scrolls=args.max_scrolls)
        
        if not jobs_data:
            logger.warning("No jobs found. Exiting.")
            return
        
        # Save the data in the requested format(s)
        if args.output_format in ['json', 'both']:
            json_file = scraper.save_to_json(jobs_data, f"{output_file}.json")
            if json_file:
                print(f"Jobs data saved to {json_file}")
        
        if args.output_format in ['csv', 'both']:
            csv_file = scraper.save_to_csv(jobs_data, f"{output_file}.csv")
            if csv_file:
                print(f"Jobs data saved to {csv_file}")
        
        print(f"Successfully scraped {len(jobs_data)} jobs for '{args.job_title}' in '{args.location}'")
        
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close the browser
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
