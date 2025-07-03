import requests
from bs4 import BeautifulSoup
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import tempfile
import shutil
import json
import xml.etree.ElementTree as ET
from tqdm import tqdm
from langdetect import detect


class PubMedPDFDownloader:
    def __init__(self):
        self.reference_pdfs = []
        self.pmcid_to_title = {}


    def get_pmid_from_title(self, title):

        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        esearch_params = {
            "db": "pubmed",
            "term": title,
            "retmode": "json",
        }
        # esearch_params = {
        #     "db": "pubmed",
        #     "term": f'"{title}"[Title]',  # use quotes and [Title] field qualifier
        #     "retmode": "json",
        #     }
        esearch_resp = requests.get(esearch_url, params=esearch_params)
        esearch_data = esearch_resp.json()

        pm_id_list = esearch_data.get("esearchresult", {}).get("idlist", [])
        return pm_id_list  # Return the list of PubMed IDs


    def remove_pmids_with_wrong_title(self, pmids, target_title):

        res = []
        for pmid in pmids:

            # Check the title with the pubmed id matches
            esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            esummary_params = {
                "db": "pubmed",
                "id": pmid,
                "retmode": "json"
            }
            esummary_resp = requests.get(esummary_url, params=esummary_params)
            esummary_data = esummary_resp.json()

            result = esummary_data.get("result", {})
            title = result.get(str(pmid), {}).get("title", None)

            if title is not None and title.strip()[:10] != target_title.strip()[:10]:
                continue
            res.append(pmid)

        return res


    def convert_pmid_to_pmcid(self, pmid, match_title=False, target_title=None):

        # Find candidate PMCID from PubMed ID
        elink_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
        elink_params = {
            "dbfrom": "pubmed",
            "db": "pmc",
            "id": pmid,
            "retmode": "json"
        }
        elink_resp = requests.get(elink_url, params=elink_params)
        elink_data = elink_resp.json()

        pmcid_candidates = []
        linksets = elink_data.get("linksets", [])
        for linkset in linksets:
            for db in linkset.get("linksetdbs", []):
                if db["dbto"] == "pmc" and db["links"]:
                    for link in db["links"]:
                        pmcid_candidates.append(f"PMC{link}")
    
            
        # Validate title from each candidate
        for pmcid in pmcid_candidates:
            # Use efetch to get the title from PMC
            efetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            efetch_params = {
                "db": "pmc",
                "id": pmcid.replace("PMC", ""),
                "retmode": "xml"
            }
            r = requests.get(efetch_url, params=efetch_params)
            if r.status_code != 200:
                continue

            # Parse title from returned XML
            try:
                root = ET.fromstring(r.content)
                language_elem = root.find(".//article-meta//language")
                if language_elem is not None and language_elem.text.strip().lower() != "en":
                    continue  # Skip non-English

                title_elem = root.find(".//article-title")
                if title_elem is not None:
                    candidate_title = "".join(title_elem.itertext()).strip()
                    # print(f"Candidate title: {candidate_title}")
                    if not match_title:
                        return pmcid, candidate_title
                    else:
                        if target_title is None:
                            raise ValueError("target_title must be provided when match_title is True")
                        if candidate_title.lower()[:10] == target_title.strip().lower()[:10]:
                            return pmcid, candidate_title
            except Exception as e:
                continue

        return None, None  # No match


    def get_raw_pmc_pdf_url(self, pmcid):

        # Step 1: Construct the article URL
        base_url = f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/'

        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
                    "AppleWebKit/537.36 (KHTML, like Gecko) " +
                    "Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Step 2: Get HTML content
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            # raise Exception(f"Failed to retrieve PMC article page: {response.status_code}")
            pass
        
        soup = BeautifulSoup(response.text, 'html.parser')
        

        # Find all <a> tags with href that ends in .pdf
        pdf_tag = soup.find('a', href=re.compile(r'\.pdf$'))
        if not pdf_tag:
            # raise Exception("PDF link not found on the PMC article page.")
            pass

        pdf_url = f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/' + pdf_tag['href']

        return pdf_url


    def download_pdf_with_selenium(self, pdf_url, download_pdf_path):
        download_dir = tempfile.mkdtemp()

        pdf_page_url = pdf_url

        chrome_path = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
        chromedriver_path = shutil.which("chromedriver")

        chrome_options = Options()
        chrome_options.binary_location = chrome_path
        chrome_options.add_argument("--headless=new")  # "new" headless mode (Chrome 109+)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,  # Bypass PDF viewer
        }
        chrome_options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
        driver.get(pdf_page_url)

        # print("Waiting for file to download...")
        time.sleep(4)  # Let JS redirect and file download begin

        # 🔍 Look for PDF file in the download folder
        downloaded_file = None
        for _ in range(10):
            files = [f for f in os.listdir(download_dir) if f.endswith(".pdf")]
            # print(len(files), "files found in download directory")
            if files:
                downloaded_file = os.path.join(download_dir, files[0])
                break
            # time.sleep(1)

        driver.quit()

        if downloaded_file:
            # print(f"PDF downloaded to: {downloaded_file}")
            os.system(f"mv '{downloaded_file}' '{download_pdf_path}'")
        else:
            # raise Exception("PDF did not download within expected time.")
            pass


    def list_from_title(self, target_title):
        candicate_ids = self.get_pmid_from_title(target_title)  # Replace with a valid title for testing
        filtered_ids = self.remove_pmids_with_wrong_title(candicate_ids, target_title)

        for pmid in filtered_ids:
            try:
                # pmcid = self.convert_pmid_to_pmcid(pmid, match_title=True, target_title=target_title)
                pmcid, title = self.convert_pmid_to_pmcid(pmid, match_title=False)
                if not pmcid or detect(title) != "en":
                    # print(f"No matching PMCID found for PMID {pmid} with title '{target_title}'")
                    continue
                
                self.pmcid_to_title[pmcid] = title

                # pdf_url = self.get_raw_pmc_pdf_url(pmcid)  # Replace with a valid PMCID for testing
                # self.download_pdf_with_selenium(pdf_url, download_pdf_path=f"{download_dir}/{pmcid}.pdf")
                self.reference_pdfs.append(pmcid)
            except Exception as e:
                print(f"Error processing PMID {pmid}: {e}")
                continue
        
    def get_download_records(self, save_path):
        saved_pdf_dict = [{"pmcid": pmcid, "title": self.pmcid_to_title[pmcid]} for pmcid in self.reference_pdfs]
        with open(save_path, "w") as f:
            for pdf in saved_pdf_dict:
                f.write(json.dumps(pdf) + "\n")



if __name__ == "__main__":

    all_chapters_dir = "/home/yishan-zhong/MIMIC-III-Agents/UpToDate-MIMIC3"
    output_dir = "/home/yishan-zhong/MIMIC-III-Agents/MIMIC3_References_PDF"
    output_metadata_dir = "/home/yishan-zhong/MIMIC-III-Agents/MIMIC3_References_Metadata"

    all_input_dirs = [
        os.path.join(all_chapters_dir, chapter)
        for chapter in os.listdir(all_chapters_dir)
        if os.path.isdir(os.path.join(all_chapters_dir, chapter))]

    for input_dir in all_input_dirs:
        print(f"Processing directory: {input_dir}")
        # input_dir = "/home/yishan-zhong/MIMIC-III-Agents/UpToDate-MIMIC3/Chapter1_infectious and parasitic diseases"
        if input_dir.startswith("Chapter1"):
            continue
        chapter_name = os.path.basename(input_dir)
        if not os.path.exists(os.path.join(output_dir, chapter_name)):
            os.makedirs(os.path.join(output_dir, chapter_name))
        pdf_save_dir = os.path.join(output_dir, chapter_name)

        with open(os.path.join(input_dir, "references.json"), "r") as f:
            references = json.load(f)

        downloader = PubMedPDFDownloader()
        for ref in tqdm(references):
            title = ref["title"]
            try:
                downloader.list_from_title(title)
            except Exception as e:
                # print(f"Error downloading PDF: {e}")
                pass
            json_save_path = os.path.join(output_metadata_dir, f"{chapter_name}_downloaded_references.jsonl".replace(" ", "_"))
            downloader.get_download_records(json_save_path)
