import tkinter as tk
from tkinter import messagebox
import asyncio
from ai_researcher import AIResearcher

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Researcher GUI")
        self.researcher = AIResearcher(headless=True)

        # Initial keyword input
        self.keyword_label = tk.Label(root, text="Enter research topic keyword:")
        self.keyword_label.pack()
        self.keyword_entry = tk.Entry(root, width=50)
        self.keyword_entry.pack()

        # Button to start research
        self.start_button = tk.Button(root, text="Start Research", command=self.start_research)
        self.start_button.pack()

        # Text area to display AI follow-up question
        self.follow_up_label = tk.Label(root, text="AI Follow-up question:")
        self.follow_up_label.pack()
        self.follow_up_text = tk.Text(root, height=5, width=50)
        self.follow_up_text.pack()

        # User response to AI follow-up question
        self.user_response_label = tk.Label(root, text="Your response:")
        self.user_response_label.pack()
        self.user_response_entry = tk.Entry(root, width=50)
        self.user_response_entry.pack()

        # Checkbox to decide whether to summarize relevant papers
        self.summarize_var = tk.BooleanVar()
        self.summarize_checkbox = tk.Checkbutton(root, text="Summarize relevant papers", variable=self.summarize_var)
        self.summarize_checkbox.pack()

        # Text area to display results
        self.results_label = tk.Label(root, text="Results:")
        self.results_label.pack()
        self.results_text = tk.Text(root, height=10, width=50)
        self.results_text.pack()

    async def research(self, keyword):
        await self.researcher.initialize()
        conversation_history = [{"role": "user", "content": f"I want to research the topic: {keyword}. Please ask me follow-up questions to refine the search."}]
        follow_up_question = await self.researcher.ask_follow_up(conversation_history)
        self.follow_up_text.insert(tk.END, follow_up_question)

        user_response = self.user_response_entry.get()
        conversation_history.append({"role": "user", "content": user_response})

        keyword_prompt = f"Extract key search keywords from this user response to use for Google Scholar search: \"{user_response}\""
        keyword_messages = [{"role": "system", "content": "You are an AI assistant that extracts concise search keywords from user input."}, {"role": "user", "content": keyword_prompt}]
        refined_keywords = self.researcher.ai_client.chat(keyword_messages).strip()

        results = await self.researcher.search_and_extract_abstracts(refined_keywords, num_results=5)
        relevant_papers = []
        for res in results:
            prompt = f"Given the research topic '{refined_keywords}', is the following paper relevant? Title: {res['title']}. Abstract: {res['snippet']}. Answer yes or no."
            messages = [{"role": "system", "content": "You are an AI assistant that determines relevance of research papers."}, {"role": "user", "content": prompt}]
            relevance = self.researcher.ai_client.chat(messages).lower()
            if "yes" in relevance:
                relevant_papers.append(res)

        self.results_text.insert(tk.END, "Relevant research papers and abstracts:\n")
        for i, res in enumerate(relevant_papers, 1):
            self.results_text.insert(tk.END, f"Paper {i}:\nTitle: {res['title']}\nURL: {res['url']}\nAbstract snippet: {res['snippet']}\n\n")

        if self.summarize_var.get():
            self.results_text.insert(tk.END, "Generating summaries...\n")
            for i, res in enumerate(relevant_papers, 1):
                title = res['title']
                abstract = res['snippet']
                summary = await self.researcher.summarize_paper(title, abstract)
                self.results_text.insert(tk.END, f"Summary of Paper {i} - {title}:\n{summary}\n\n")

        await self.researcher.close()

    def start_research(self):
        keyword = self.keyword_entry.get()
        if not keyword:
            messagebox.showerror("Error", "Keyword cannot be empty.")
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.research(keyword))

if __name__ == "__main__":
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()
