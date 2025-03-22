from bs4 import BeautifulSoup
import os
from langchain.document_loaders import Docx2txtLoader
from PyPDF2 import PdfReader
import re
import subprocess
import tempfile
from pdf2image import convert_from_path
import pytesseract

class Parser:
    def __init__(self, path: str = 'docs') -> None:
        self.path = path

    def extract_text_from_html(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            text = soup.get_text(separator=' ')
            text = " ".join(text.split())
            
            return text
        except UnicodeDecodeError as e:
            raise RuntimeError(f"Ошибка кодировки файла: {e}")
        except Exception as e:
            raise RuntimeError(f"Ошибка при обработке HTML: {e}")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text()
            
            text = " ".join(text.split())
            
            return text
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF файл не найден: {file_path}")
        except PermissionError:
            raise PermissionError(f"Нет доступа к файлу: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Ошибка при обработке PDF: {e}")
    
    def extract_text_from_docx(self, file_path: str) -> str:
        try:
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
            
            text = " ".join([doc.page_content for doc in documents])
            
            text = " ".join(text.split())
            
            return text
        except FileNotFoundError:
            raise FileNotFoundError(f"DOCX файл не найден: {file_path}")
        except PermissionError:
            raise PermissionError(f"Нет доступа к файлу: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Ошибка при обработке DOCX: {e}")

    def extract_text_from_djvu(self, file_path: str) -> str:
        """
        Извлекает текст из файла DjVu с помощью утилиты djvutxt.

        Аргументы:
            file_path (str): Путь к файлу DjVu

        Возвращает:
            str: Извлеченный текст

        Исключения:
            FileNotFoundError: Если файл не существует
            RuntimeError: При ошибках извлечения текста
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Файл {file_path} не существует")

        try:
            result = subprocess.run(
                ["C:\Program Files (x86)\DjVuLibre\djvutxt.exe", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Ошибка извлечения текста: {e.stderr}") from e
        except FileNotFoundError:
            raise RuntimeError(
                "Утилита djvutxt не найдена. Установите DjVuLibre:\n"
                "Linux: sudo apt-get install djvulibre-bin\n"
                "MacOS: brew install djvulibre\n"
                "Windows: скачайте с https://djvu.sourceforge.net/"
            ) from None
        except PermissionError:
            raise PermissionError(f"Нет прав на выполнение djvutxt")
    
    def parse_document(self, file_path: str, inner_text: bool = False) -> str:
        if not inner_text:
            file_path = os.path.join(self.path, file_path)
        try:
            _, extension = os.path.splitext(file_path)
            extension = extension.lower()

            if extension == '.html':
                return self.extract_text_from_html(file_path)
            elif extension == '.pdf':
                return self.extract_text_from_pdf(file_path)
            elif extension == '.docx':
                return self.extract_text_from_docx(file_path)
            elif extension == '.djvu':
                return self.extract_text_from_djvu(file_path)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {extension}")
        except (FileNotFoundError, PermissionError) as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"Непредвиденная ошибка при обработке {file_path}: {e}")

    def find_links(self, text: str) -> list[str]:
        try:
            url_pattern = re.compile(r'https?://\S+|www\.\S+')
            links = url_pattern.findall(text)
            return links
        except Exception as e:
            raise RuntimeError(f"Ошибка при поиске ссылок: {e}")
    
    def process_documents(self) -> dict[str, tuple[str, list[str]]]:
        documents_text = {}
        folder_path = self.path

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            if filename.lower().endswith(('.html', '.pdf', '.docx', '.djvu')):
                try:
                    # print(f"Обработка файла: {filename}")
                    text = self.parse_document(file_path, inner_text=True)
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
