import asyncio
from pyppeteer import launch
from urllib.parse import quote_plus

class AIResearcher:
    def __init__(self, headless=True, timeout=30000):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.page = None

    async def initialize(self):
        self.browser = await launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        self.page = await self.browser.newPage()
        await self.page.setViewport({'width': 1280, 'height': 800})
        await self.page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        )
        await self.page.setExtraHTTPHeaders({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    async def close(self):
        if self.browser:
            await self.browser.close()

    async def search_and_extract_abstracts(self, keyword, num_results=5):
        encoded_query = quote_plus(keyword)
        search_url = f"https://scholar.google.com/scholar?q={encoded_query}"

        try:
            await self.page.goto(search_url, {'timeout': self.timeout, 'waitUntil': 'networkidle0'})
        except Exception as e:
            print(f"Error loading page: {e}")
            return []

        try:
            await self.page.waitForSelector('.gs_r', {'timeout': self.timeout})
        except Exception as e:
            print(f"Timeout waiting for search results: {e}")
            return []

        results = await self.page.evaluate('''() => {
            const entries = Array.from(document.querySelectorAll('.gs_r'));
            return entries.slice(0, 5).map(entry => {
                const titleElem = entry.querySelector('.gs_rt a');
                const title = titleElem ? titleElem.innerText : 'No title';
                const url = titleElem ? titleElem.href : null;
                const snippetElem = entry.querySelector('.gs_rs');
                const snippet = snippetElem ? snippetElem.innerText : 'No abstract snippet';
                return {title, url, snippet};
            });
        }''')

        return results

async def main():
    print("AI Enabled Researcher - Abstract Scraper")
    keyword = input("Enter research topic keyword: ").strip()
    if not keyword:
        print("Keyword cannot be empty.")
        return

    researcher = AIResearcher(headless=True)
    await researcher.initialize()
    print(f"Searching Google Scholar for keyword: {keyword}")
    results = await researcher.search_and_extract_abstracts(keyword, num_results=5)
    await researcher.close()

    if not results:
        print("No results found.")
        return

    print("\nTop research papers and abstracts:")
    for i, res in enumerate(results, 1):
        print(f"\nPaper {i}:")
        print(f"Title: {res['title']}")
        print(f"URL: {res['url']}")
        print(f"Abstract snippet: {res['snippet']}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
