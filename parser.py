from bs4 import BeautifulSoup
import os
from langchain.document_loaders import Docx2txtLoader
from PyPDF2 import PdfReader
import re

class Parser:
    def __init__(self, path='docs'):
        self.path = path

    def extract_text_from_html(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        text = soup.get_text(separator=' ')
        text = " ".join(text.split())
        
        return text
    
    def extract_text_from_pdf(self, file_path):
        reader = PdfReader(file_path)
        text = ""
        
        for page in reader.pages:
            text += page.extract_text()
        
        text = " ".join(text.split())
        
        return text
    
    def extract_text_from_docx(self, file_path):
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        
        text = " ".join([doc.page_content for doc in documents])
        
        text = " ".join(text.split())
        
        return text
    
    def parse_document(self, file_path):
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        if extension == '.html':
            return self.extract_text_from_html(file_path)
        elif extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {extension}")

    def find_links(self, text):
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        links = url_pattern.findall(text)
        return links
    
    def process_documents(self):
        documents_text = {}
        folder_path = self.path

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            if filename.lower().endswith(('.html', '.pdf', '.docx')):
                try:
                    print(f"Обработка файла: {filename}")
                    text = self.parse_document(file_path)
                    links = self.find_links(text)
                    documents_text[filename] = (text, links)
                except Exception as e:
                    print(f"Ошибка при обработке файла {filename}: {e}")
            else:
                print(f"Файл {filename} пропущен (неподдерживаемый формат).")

        return documents_text

if __name__ == '__main__':
    parser = Parser()
    data = parser.process_documents()
    print(data)
