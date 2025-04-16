import json
from typing import Dict, List
from parsel import Selector
from loguru import logger as log
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapeApiResponse

SCRAPFLY = ScrapflyClient(key="scp-live-746c367002994e48903df0c7af5f0fba")

BASE_CONFIG = {
    # bypass linkedin.com web scraping blocking
    "asp": True,
    # set the proxy country to US
    "country": "US",
    "headers": {
        "Accept-Language": "en-US,en;q=0.5"
    }
}

def refine_profile(data: Dict) -> Dict: 
    """refine and clean the parsed profile data"""
    parsed_data = {}
    profile_data = [key for key in data["@graph"] if key["@type"]=="Person"][0]
    profile_data["worksFor"] = [profile_data["worksFor"][0]]
    articles = [key for key in data["@graph"] if key["@type"]=="Article"]
    for article in articles:
        selector = Selector(article["articleBody"])
        article["articleBody"] = "".join(selector.xpath("//p/text()").getall())
    parsed_data["profile"] = profile_data
    parsed_data["posts"] = articles
    return parsed_data


def parse_profile(response: ScrapeApiResponse) -> Dict:
    """parse profile data from hidden script tags"""
    selector = response.selector
    data = json.loads(selector.xpath("//script[@type='application/ld+json']/text()").get())
    refined_data = refine_profile(data)
    return refined_data


async def scrape_profile(urls: List[str]) -> List[Dict]:
    """scrape public linkedin profile pages"""
    to_scrape = [ScrapeConfig(url, **BASE_CONFIG) for url in urls]
    data = []
    # scrape the URLs concurrently
    async for response in SCRAPFLY.concurrent_scrape(to_scrape):
        profile_data = parse_profile(response)
        data.append(profile_data)
    log.success(f"scraped {len(data)} profiles from Linkedin")
    return data