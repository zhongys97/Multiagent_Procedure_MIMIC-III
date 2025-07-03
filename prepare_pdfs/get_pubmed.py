import requests
from bs4 import BeautifulSoup
import os
import re
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import tempfile

def get_raw_pmc_pdf_url(pmcid, save_dir='./'):
    # Step 1: Construct the article URL
    # base_url = f'https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/'
    base_url = f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/'

    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
                  "AppleWebKit/537.36 (KHTML, like Gecko) " +
                  "Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print(base_url)
    # Step 2: Get HTML content
    response = requests.get(base_url, headers=headers)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve PMC article page: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # print(soup.prettify())  # Debugging line to check the HTML content
    # Step 3: Find the PDF link
    # pdf_link = soup.find('a', string='PDF')
    # if not pdf_link:
    #     raise Exception("PDF link not found on the PMC article page.")

    # Find all <a> tags with href that ends in .pdf
    pdf_tag = soup.find('a', href=re.compile(r'\.pdf$'))
    if not pdf_tag:
        raise Exception("PDF link not found on the PMC article page.")

    print("PDF Tag:", pdf_tag)  # Debugging line to check the PDF tag
    pdf_url = f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/' + pdf_tag['href']
    # pdf_url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC9446823/pdf/13063_2022_Article_6681.pdf"
    # pdf_url = "https://www.ncbi.nlm.nih.gov/articles/PMC9446823/pdf/13063_2022_Article_6681.pdf"

    print(f"PDF URL: {pdf_url}")  # Debugging line to check the PDF URL
    return pdf_url


def download_pdf_with_selenium(pdf_url):
    # url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
    url = pdf_url

    chrome_options = Options()
    chrome_options.headless = True
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # Wait for PoW to complete
    time.sleep(10)

    # Final PDF URL
    final_url = driver.current_url
    driver.quit()

    print("Resolved PDF URL:", final_url)
    return final_url


    # # Step 4: Download the PDF
    # pdf_response = requests.get(pdf_url, headers=headers)
    # if pdf_response.status_code != 200:
    #     raise Exception(f"Failed to download PDF: {pdf_response.status_code}")
    
    # # Step 5: Save the PDF
    # filename = os.path.join(save_dir, f"{pmcid}.pdf")
    # with open(filename, 'wb') as f:
    #     f.write(pdf_response.content)
    
    # print(f"Downloaded PDF for {pmcid} to {filename}")

    # filename = os.path.join(save_dir, f"{pmcid}.pdf")
    # command = ["wget", "-O", filename, pdf_url]
    # result = subprocess.run(command, capture_output=True)

    # if result.returncode != 0:
    #     raise Exception(f"wget failed: {result.stderr.decode()}")

    # print(f"Downloaded with wget to {filename}")

def get_pmcid_from_title(title, author_lastname, year):
    # Step 1: Search PubMed for the title
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    esearch_params = {
        "db": "pubmed",
        "term": title,
        "retmode": "json",
    }

    # query = f'"{title}"[Title] AND {year}[PDAT]'
    # query = f'"{title}"[Title]'

    # esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    # esearch_params = {
    #     "db": "pubmed",
    #     "term": query,
    #     "retmode": "json",
    # }

    esearch_resp = requests.get(esearch_url, params=esearch_params)
    esearch_data = esearch_resp.json()

    id_list = esearch_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return None

    print("Search Results:", esearch_data.get("esearchresult", {}))  # Debugging line to check the search results
    print("ID List:", id_list)  # Debugging line to check the ID list
    pmid = id_list[0]

    # Step 2: Use elink to find the PMCID from the PMID
    elink_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    elink_params = {
        "dbfrom": "pubmed",
        "db": "pmc",
        "id": pmid,
        "retmode": "json"
    }
    elink_resp = requests.get(elink_url, params=elink_params)
    elink_data = elink_resp.json()

    linksets = elink_data.get("linksets", [])
    if not linksets:
        return None

    pmcid = None
    for linksetdb in linksets[0].get("linksetdbs", []):
        if linksetdb["dbto"] == "pmc":
            pmcid = linksetdb["links"][0]
            break

    if pmcid:
        return f"PMC{pmcid}"
    else:
        return None

# # Example usage
# title = "Validity of the CRAFFT substance abuse screening test among adolescent clinic patients"
# pmcid = get_pmcid_from_title(title, None, None)
# print(f"PMCID: {pmcid}")
# if pmcid:
#     download_pmc_pdf(pmcid, save_dir='./')

pdf_url = get_raw_pmc_pdf_url('PMC9446823', save_dir='./')  # Replace with a valid PMCID for testing
protected_url = download_pdf_with_selenium(pdf_url)
print(f"Protected PDF URL: {protected_url}")