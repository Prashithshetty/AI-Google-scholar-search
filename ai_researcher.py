import asyncio
from pyppeteer import launch
from urllib.parse import quote_plus
from ai_chat_client import AIChatClient

class AIResearcher:
    def __init__(self, headless=True, timeout=30000):
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.page = None
        self.ai_client = AIChatClient()

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

    async def ask_follow_up(self, conversation_history):
        messages = [{"role": "system", "content": "You are an AI research assistant."}]
        messages.extend(conversation_history)
        response = self.ai_client.chat(messages)
        return response

    async def summarize_paper(self, title, abstract):
        prompt = f"Summarize the following research paper titled '{title}' into key points:\n\n{abstract}"
        messages = [
            {"role": "system", "content": "You are an AI assistant that summarizes research papers into concise key points."},
            {"role": "user", "content": prompt}
        ]
        summary = self.ai_client.chat(messages)
        return summary

async def main():
    print("AI Enabled Researcher - Abstract Scraper with AI Integration")
    researcher = AIResearcher(headless=True)
    await researcher.initialize()

    # Initial keyword input
    keyword = input("Enter research topic keyword: ").strip()
    if not keyword:
        print("Keyword cannot be empty.")
        await researcher.close()
        return

    conversation_history = [
        {"role": "user", "content": f"I want to research the topic: {keyword}. Please ask me follow-up questions to refine the search."}
    ]

    # Generate follow-up question from AI
    follow_up_question = await researcher.ask_follow_up(conversation_history)
    print(f"\nAI Follow-up question: {follow_up_question}")

    # Get user response to follow-up question
    user_response = input("Your response: ").strip()
    conversation_history.append({"role": "user", "content": user_response})

    # Use AI to analyze user response and generate refined keywords
    keyword_prompt = f"Extract key search keywords from this user response to use for Google Scholar search: \"{user_response}\""
    keyword_messages = [
        {"role": "system", "content": "You are an AI assistant that extracts concise search keywords from user input."},
        {"role": "user", "content": keyword_prompt}
    ]
    refined_keywords = researcher.ai_client.chat(keyword_messages).strip()

    print(f"\nSearching Google Scholar for refined keywords: {refined_keywords}")
    results = await researcher.search_and_extract_abstracts(refined_keywords, num_results=5)

    if not results:
        print("No results found.")
        await researcher.close()
        return

    # Analyze abstracts for relevance using AI (simple prompt)
    relevant_papers = []
    for res in results:
        prompt = f"Given the research topic '{refined_keywords}', is the following paper relevant? Title: {res['title']}. Abstract: {res['snippet']}. Answer yes or no."
        messages = [
            {"role": "system", "content": "You are an AI assistant that determines relevance of research papers."},
            {"role": "user", "content": prompt}
        ]
        relevance = researcher.ai_client.chat(messages).lower()
        if "yes" in relevance:
            relevant_papers.append(res)

    if not relevant_papers:
        print("No relevant papers found after analysis.")
        await researcher.close()
        return

    print("\nRelevant research papers and abstracts:")
    for i, res in enumerate(relevant_papers, 1):
        print(f"\nPaper {i}:")
        print(f"Title: {res['title']}")
        print(f"URL: {res['url']}")
        print(f"Abstract snippet: {res['snippet']}")

    # Ask user if they want summaries
    summarize = input("\nWould you like the AI to summarize each relevant paper? (yes/no): ").strip().lower()
    if summarize in ['yes', 'y']:
        print("\nGenerating summaries...")
        for i, res in enumerate(relevant_papers, 1):
            title = res['title']
            abstract = res['snippet']
            summary = await researcher.summarize_paper(title, abstract)
            print(f"\nSummary of Paper {i} - {title}:\n{summary}")

    await researcher.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
