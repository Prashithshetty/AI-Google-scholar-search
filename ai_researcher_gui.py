import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import asyncio
import threading
from ai_researcher import AIResearcher

class ResearchThread(QThread):
    result_ready = pyqtSignal(str)

    def __init__(self, keyword):
        super().__init__()
        self.keyword = keyword

    def run(self):
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        researcher = AIResearcher(headless=True)
        # Run the async initialize and research in the new event loop
        loop.run_until_complete(researcher.initialize())
        result_text = loop.run_until_complete(self.perform_research(researcher, self.keyword))
        loop.run_until_complete(researcher.close())
        self.result_ready.emit(result_text)

    async def perform_research(self, researcher, keyword):
        results = await researcher.search_and_extract_abstracts(keyword, num_results=5)
        if not results:
            return "No results found."
        output = "Top research papers and abstracts:\n"
        for i, res in enumerate(results, 1):
            output += f"\nPaper {i}:\nTitle: {res['title']}\nURL: {res['url']}\nAbstract snippet: {res['snippet']}\n"
        return output

class AIResearcherGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Enabled Researcher")
        self.setGeometry(100, 100, 800, 600)
        self.layout = QVBoxLayout()

        self.label = QLabel("Enter research topic keyword:")
        self.layout.addWidget(self.label)

        self.input = QLineEdit()
        self.layout.addWidget(self.input)

        self.search_button = QPushButton("Start Research")
        self.search_button.clicked.connect(self.start_research)
        self.layout.addWidget(self.search_button)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

        self.setLayout(self.layout)

    def start_research(self):
        keyword = self.input.text().strip()
        if not keyword:
            self.output.setText("Please enter a research topic keyword.")
            return
        self.output.setText("Research started...\n")
        self.search_button.setEnabled(False)
        self.thread = ResearchThread(keyword)
        self.thread.result_ready.connect(self.display_results)
        self.thread.start()

    def display_results(self, text):
        self.output.setText(text)
        self.search_button.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    window = AIResearcherGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
