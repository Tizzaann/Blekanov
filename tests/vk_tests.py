import vk_api
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import calendar
import configparser
import unittest
from vk import VKUniversityMentionsCollector
import json
from pathlib import Path


class VKAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Используем реальный тестовый токен"""


        config = configparser.ConfigParser()
        config.read('config.ini')

        cls.TEST_TOKEN = config['vk']['access_token']

        if not cls.TEST_TOKEN:
            raise ValueError("Нет токена")
        
        # Тестовые университеты (не влияют на реальные данные)
        cls.TEST_UNIVERSITIES = ["СПбГУ", "МГУ", "UsandiPA0s"]

    def test_real_api_search(self):
        """Тест работоспособности"""
        collector = VKUniversityMentionsCollector(self.TEST_TOKEN)
        
        # Ищем за последние 24 часа чтобы получить актуальные, но не старые данные
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=5)).timestamp())
        
        posts = collector.search_posts(
            query=self.TEST_UNIVERSITIES[0],
            start_time=start_time,
            end_time=end_time,
            count=10
        )
        
        # Проверяем структуру ответа
        if posts:  # Может быть пустым, если нет постов
            post = posts[0]
            self.assertIn('id', post)
            self.assertIn('text', post)
            self.assertTrue(isinstance(post.get('date', 0), int))

    def test_error_handling(self):
        """Тест обработки ошибок API"""
        collector = VKUniversityMentionsCollector(self.TEST_TOKEN)
        
        # Неправильный запрос (слишком длинный)
        with self.assertRaises(vk_api.exceptions.ApiError):
            collector.search_posts(
                query="X" * 300,  # Слишком длинный запрос
                start_time=0,
                end_time=0
            )

    def test_print_university_stats(self):
        """Тест вывода статистики по университету"""
        
        collector = VKUniversityMentionsCollector(self.TEST_TOKEN)
        collector.university_stats = {
            "СПбГУ": {
                'posts_count': 5,
                'authors_count': 3,
                'likes_count': 100,
                'views_count': 1000,
                'reposts_count': 20,
                'comments_count': 30
            }
        }
        
        # Перенаправляем stdout для проверки вывода
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        collector.print_university_stats("СПбГУ")
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        self.assertIn("СТАТИСТИКА ПО УНИВЕРСИТЕТУ: СПбГУ", output)
        self.assertIn("Количество публикаций: 5", output)
    
    def test_print_overall_stats(self):
        """Тест вывода общей статистики"""

        collector = VKUniversityMentionsCollector(self.TEST_TOKEN)
        collector.data = [1, 2, 3]  # Просто 3 элемента
        collector.unique_authors = {1, 2}
        
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        collector.print_overall_stats()
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        self.assertIn("ОБЩАЯ СТАТИСТИКА ПО ВСЕМ УНИВЕРСИТЕТАМ", output)
        self.assertIn("Общее количество публикаций: 3", output)



if __name__ == '__main__':
    unittest.main()