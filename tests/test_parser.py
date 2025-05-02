# python -m unittest test_parser.py -v чтобы запустить тесты подробно

import unittest
import os
from parser import Parser
from colorama import Fore, Style, init
import time
import re

init(autoreset=True)  # Инициализация colorama

class TestParser(unittest.TestCase):
    successful_tests = []  # Успешно обработанные файлы
    unsupported_files = set()  # Используем SET для удаления дубликатов

    @classmethod
    def setUpClass(cls):
        """Инициализация перед запуском всех тестов"""
        cls.test_folder = "docs"
        cls.parser = Parser()
        cls.test_files = {"html": [], "pdf": [], "docx": []}
        cls.bad_character_files = []
        cls.clean_files = []

        if not os.path.exists(cls.test_folder):
            raise unittest.SkipTest(f"Папка '{cls.test_folder}' отсутствует. Создай её вручную и добавь файлы.")

        # Поиск файлов нужных форматов
        for file in os.listdir(cls.test_folder):
            if file.endswith(".html"):
                cls.test_files["html"].append(file)
            elif file.endswith(".pdf"):
                cls.test_files["pdf"].append(file)
            elif file.endswith(".docx"):
                cls.test_files["docx"].append(file)
            else:
                cls.unsupported_files.add(file)

    def setUp(self):
        """Подготовка перед каждым тестом"""
        self.files_with_links = []
        self.files_without_links = []
        self.encoding_issues = []

    def print_status(self, filenames, test_name, success):
        """Выводит результат теста"""
        if success:
            status = f"{Fore.GREEN}Успешен{Style.RESET_ALL}"
            TestParser.successful_tests.extend(filenames)
        else:
            status = f"{Fore.RED}Не успешен{Style.RESET_ALL}"

        files_str = ", ".join(filenames) if filenames else "Нет файлов"
        print(f"{Fore.GREEN}Файл(ы): {files_str}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Тест {test_name}: {status}{Style.RESET_ALL}\n")

    def test_extract_text_from_html(self):
        """Тест: Извлечение текста из HTML"""
        if not self.test_files["html"]:
            self.skipTest("Файлы .html не найдены.")

        successful_files = []
        for filename in self.test_files["html"]:
            file_path = os.path.join(self.test_folder, filename)
            text = self.parser.extract_text_from_html(file_path)
            if len(text) > 0:
                successful_files.append(filename)

        self.print_status(successful_files, "извлечение текста из HTML", len(successful_files) > 0)
        self.assertGreater(len(successful_files), 0, "Ни один HTML-файл не был успешно обработан.")

    def test_extract_text_from_pdf(self):
        """Тест: Извлечение текста из PDF"""
        if not self.test_files["pdf"]:
            self.skipTest("Файлы .pdf не найдены.")

        successful_files = []
        for filename in self.test_files["pdf"]:
            file_path = os.path.join(self.test_folder, filename)
            text = self.parser.extract_text_from_pdf(file_path)
            if len(text) > 0:
                successful_files.append(filename)

        self.print_status(successful_files, "извлечение текста из PDF", len(successful_files) > 0)
        self.assertGreater(len(successful_files), 0, "Ни один PDF-файл не был успешно обработан.")

    def test_extract_text_from_docx(self):
        """Тест: Извлечение текста из DOCX"""
        if not self.test_files["docx"]:
            self.skipTest("Файлы .docx не найдены.")

        successful_files = []
        for filename in self.test_files["docx"]:
            file_path = os.path.join(self.test_folder, filename)
            text = self.parser.extract_text_from_docx(file_path)
            if len(text) > 0:
                successful_files.append(filename)

        self.print_status(successful_files, "извлечение текста из DOCX", len(successful_files) > 0)
        self.assertGreater(len(successful_files), 0, "Ни один DOCX-файл не был успешно обработан.")

    def test_find_links_in_files(self):
        """Тест: Поиск ссылок во всех файлах"""
        all_files = self.test_files["html"] + self.test_files["pdf"] + self.test_files["docx"]

        if not all_files:
            self.skipTest("Файлы для поиска ссылок не найдены.")

        for filename in all_files:
            file_path = os.path.join(self.test_folder, filename)
            try:
                # Определяем формат и извлекаем текст
                if filename.endswith(".html"):
                    text = self.parser.extract_text_from_html(file_path)
                elif filename.endswith(".pdf"):
                    text = self.parser.extract_text_from_pdf(file_path)
                elif filename.endswith(".docx"):
                    text = self.parser.extract_text_from_docx(file_path)
                else:
                    continue

                # Ищем ссылки
                links = self.parser.find_links(text)
                if links:
                    self.files_with_links.append(filename)
                else:
                    self.files_without_links.append(filename)

            except Exception as e:
                print(f"{Fore.RED}Ошибка при обработке {filename}: {e}{Style.RESET_ALL}")

        # Вывод результатов
        print(f"\n{Fore.CYAN}Файлы с найденными ссылками: {', '.join(self.files_with_links) if self.files_with_links else 'Нет'}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Файлы без ссылок: {', '.join(self.files_without_links) if self.files_without_links else 'Нет'}{Style.RESET_ALL}\n")

        self.assertGreater(len(self.files_with_links) + len(self.files_without_links), 0, "Ни один файл не был обработан.")

    def test_unsupported_files(self):
     """Тест: Нахождение неподдерживаемых файлов"""
     if not self.unsupported_files:
        self.skipTest("Неподдерживаемые файлы не найдены.")
        print(f"{Fore.YELLOW}Файлы неподдерживаемых форматов: {', '.join(self.unsupported_files)}{Style.RESET_ALL}")
        self.assertGreater(len(self.unsupported_files), 0, "Неподдерживаемые файлы должны быть найдены.")

  

    def test_parser_performance(self):
        """Тест: Проверка скорости работы парсера"""
        all_files = self.test_files["html"] + self.test_files["pdf"] + self.test_files["docx"]
        if not all_files:
            self.skipTest("Нет файлов для тестирования производительности.")

        start_time = time.time()

        for filename in all_files:
            file_path = os.path.join(self.test_folder, filename)
            try:
                if filename.endswith(".html"):
                    self.parser.extract_text_from_html(file_path)
                elif filename.endswith(".pdf"):
                    self.parser.extract_text_from_pdf(file_path)
                elif filename.endswith(".docx"):
                    self.parser.extract_text_from_docx(file_path)
            except Exception as e:
                print(f"{Fore.RED}Ошибка при обработке {filename}: {e}{Style.RESET_ALL}")

        duration = time.time() - start_time
        
        print(f"{Fore.MAGENTA}Тест производительности: выполнено за {duration:.3f} секунд{Style.RESET_ALL}")

        self.assertLess(duration, 10, f"Парсер работает слишком медленно: {duration:.10f} секунд")

    def test_character_processing_speed(self):
        """Тест: Проверка скорости обработки символов"""
        all_files = self.test_files["html"] + self.test_files["pdf"] + self.test_files["docx"]
        if not all_files:
            self.skipTest("Нет файлов для тестирования производительности.")
        
        start_time = time.time()
        total_chars = 0
        for filename in all_files:
            file_path = os.path.join(self.test_folder, filename)
            try:
                if filename.endswith(".html"):
                    text = self.parser.extract_text_from_html(file_path)
                elif filename.endswith(".pdf"):
                    text = self.parser.extract_text_from_pdf(file_path)
                elif filename.endswith(".docx"):
                    text = self.parser.extract_text_from_docx(file_path)
                else:
                    continue
                total_chars += len(text)
            except Exception as e:
                print(f"{Fore.RED}Ошибка при обработке {filename}: {e}{Style.RESET_ALL}")
        
        duration = time.time() - start_time
        speed = total_chars / max(duration, 0.001)
        print(f"{Fore.MAGENTA}Тест скорости обработки: {speed:.2f} символов/сек{Style.RESET_ALL}")
        self.assertGreater(speed, 100, "Скорость обработки слишком низкая (< 100 символов/сек)")
    
    def test_utf8_encoding(self):
        """Тест: Проверка кодировки файлов (UTF-8)"""
        all_files = self.test_files["html"] + self.test_files["pdf"] + self.test_files["docx"]
        if not all_files:
            self.skipTest("Нет файлов для проверки кодировки.")
        
        for filename in all_files:
            file_path = os.path.join(self.test_folder, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read()
            except (UnicodeDecodeError, IOError):
                self.encoding_issues.append(filename)
        
        print(f"{Fore.YELLOW}Файлы с проблемами кодировки: {', '.join(self.encoding_issues) if self.encoding_issues else 'Нет'}{Style.RESET_ALL}")
        self.assertEqual(len(self.encoding_issues), 0, "Некоторые файлы не соответствуют UTF-8.")

    def test_bad_character_ratio(self):
        """Тест: Проверка количества плохих символов в файлах"""
        all_files = self.test_files["html"] + self.test_files["pdf"] + self.test_files["docx"]
        if not all_files:
            self.skipTest("Нет файлов для тестирования плохих символов.")
        
        for filename in all_files:
            file_path = os.path.join(self.test_folder, filename)
            try:
                if filename.endswith(".html"):
                    text = self.parser.extract_text_from_html(file_path)
                elif filename.endswith(".pdf"):
                    text = self.parser.extract_text_from_pdf(file_path)
                elif filename.endswith(".docx"):
                    text = self.parser.extract_text_from_docx(file_path)
                else:
                    continue
                
                bad_chars = len(re.findall(r'[^\x00-\x7F]', text))
                if bad_chars / max(1, len(text)) > 0.5:
                    self.bad_character_files.append(filename)
                else:
                    self.clean_files.append(filename)
            except Exception as e:
                print(f"{Fore.RED}Ошибка при обработке {filename}: {e}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}Файлы без иероглифов: {', '.join(self.clean_files) if self.clean_files else 'Нет'}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Файлы с иероглифами: {', '.join(self.bad_character_files) if self.bad_character_files else 'Нет'}{Style.RESET_ALL}")
        self.assertEqual(len(self.bad_character_files), 0, "Некоторые файлы содержат более 50% плохих символов.")

    @classmethod
    def tearDownClass(cls):
        """Выводит итоговый отчет после всех тестов"""
        print("\n" + "="*60)

        if cls.successful_tests:
            print(f"{Fore.CYAN}Все файлы в папке docs прошли тестирование: {', '.join(set(cls.successful_tests))}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Ни один файл не был успешно обработан.{Style.RESET_ALL}")

        if cls.unsupported_files:
            print(f"{Fore.YELLOW}Файлы неподдерживаемых форматов: {', '.join(cls.unsupported_files)}{Style.RESET_ALL}")

        print("="*60 + "\n")


if __name__ == "__main__":
    unittest.main()