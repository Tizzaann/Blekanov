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

class VKUniversityMentionsCollector:
    def __init__(self, access_token):
        """
        Инициализация сборщика данных о упоминаниях университетов
        :param access_token: Токен доступа VK API
        """
        self.access_token = access_token
        self.vk_session = vk_api.VkApi(token=access_token)
        self.vk = self.vk_session.get_api()
        self.data = []
        self.unique_authors = set()
        self.university_stats = {}

    def search_posts(self, query, start_time, end_time, count=100):
        """
        Поиск публикаций по запросу за определенный период
        :param query: Поисковый запрос
        :param start_time: Время начала периода поиска
        :param end_time: Время окончания периода поиска
        :param count: Максимальное количество записей в одном запросе
        :return: Словарь с результатами поиска
        """
        posts_found = []
        offset = 0
        total_count = 1  # Начальное значение для входа в цикл
        
        while offset < total_count and offset < 1000:  # API ограничение - максимум 1000 записей
            try:
                
                response = self.vk.newsfeed.search(
                    q=query,
                    start_time=start_time,
                    end_time=end_time,
                    count=count,
                    offset=offset
                )
                
                # Устанавливаем общее количество найденных записей
                if offset == 0:
                    total_count = min(response['total_count'], 1000)
                
                # Добавляем найденные записи
                if 'items' in response:
                    posts_found.extend(response['items'])
                
                offset += count
                
                # Задержка для избежания превышения лимита запросов
                time.sleep(0.5)
                
            except vk_api.exceptions.ApiError as e:
                print(f"Ошибка API: {e}")
                break
                
        return posts_found

    def collect_data(self, universities, year=2024):
        """
        Сбор данных о упоминаниях университетов за указанный год
        :param universities: Список университетов для поиска
        :param year: Год, за который собираются данные
        """
        # Устанавливаем период поиска: весь указанный год
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31, 23, 59, 59)
        
        # Если указанный год - текущий, то конечная дата - текущая дата
        if year == datetime.now().year:
            end_date = datetime.now()
        
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        print(f"Период поиска: с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}")
        
        for university in universities:
            print(f"\nПоиск упоминаний: {university}")
            
            # Ищем публикации для каждого университета
            posts = self.search_posts(university, start_timestamp, end_timestamp)
            
            if not posts:
                print(f"Публикации для '{university}' не найдены")
                continue
            
            print(f"Найдено {len(posts)} публикаций для '{university}'")
            
            # Переменные для статистики по текущему университету
            university_posts = []
            university_authors = set()
            university_likes = 0
            university_views = 0
            university_reposts = 0
            university_comments = 0

            for i, post in enumerate(posts):
                timestamp = post.get('date', 0)
                date = datetime.fromtimestamp(timestamp)
                if i < 10:
                    print(f"Raw timestamp: {timestamp}, Date: {date}")
                else:
                    break

            for post in tqdm(posts, desc=f"Обработка публикаций {university}"):
                try:
                    # Извлекаем необходимые данные из публикации
                    post_data = {
                        'university': university,
                        'post_id': post.get('id', ''),
                        'owner_id': post.get('owner_id', ''),
                        'author_id': post.get('from_id', post.get('owner_id', '')),
                        'date': datetime.fromtimestamp(post.get('date', 0)),
                        'text': post.get('text', ''),
                        'likes': post.get('likes', {}).get('count', 0),
                        'views': post.get('views', {}).get('count', 0) if 'views' in post else 0,
                        'reposts': post.get('reposts', {}).get('count', 0),
                        'comments': post.get('comments', {}).get('count', 0),
                        'post_url': f"https://vk.com/wall{post.get('owner_id', '')}_{post.get('id', '')}"
                    }
                    
                    # Проверяем, что публикация относится к указанному году
                    post_year = post_data['date'].year
                    if post_year != year:
                        continue
                    
                    # Добавляем данные в общий список
                    self.data.append(post_data)
                    university_posts.append(post_data)
                    
                    # Обновляем множество всех авторов
                    self.unique_authors.add(post_data['author_id'])
                    university_authors.add(post_data['author_id'])
                    
                    # Накапливаем статистику
                    university_likes += post_data['likes']
                    university_views += post_data['views']
                    university_reposts += post_data['reposts']
                    university_comments += post_data['comments']
                    
                except Exception as e:
                    print(f"Ошибка при обработке публикации: {e}")
            
            # Сохраняем статистику по университету
            self.university_stats[university] = {
                'posts_count': len(university_posts),
                'authors_count': len(university_authors),
                'likes_count': university_likes,
                'views_count': university_views,
                'reposts_count': university_reposts,
                'comments_count': university_comments,
                'posts_data': university_posts  # Сохраняем данные для построения графика
            }
            
            # Выводим статистику по текущему университету
            self.print_university_stats(university)
    
    def print_university_stats(self, university):
        """
        Вывод статистики по университету
        :param university: Название университета
        """
        stats = self.university_stats.get(university)
        if not stats:
            print(f"Нет статистики для университета {university}")
            return
        
        print("\n" + "=" * 50)
        print(f"СТАТИСТИКА ПО УНИВЕРСИТЕТУ: {university}")
        print("=" * 50)
        print(f"Количество публикаций: {stats['posts_count']}")
        print(f"Количество авторов: {stats['authors_count']}")
        print(f"Общее количество лайков: {stats['likes_count']}")
        print(f"Общее количество просмотров: {stats['views_count']}")
        print(f"Общее количество репостов: {stats['reposts_count']}")
        print(f"Общее количество комментариев: {stats['comments_count']}")
        print("=" * 50)
    
    def plot_monthly_posts(self, year=2024, filename="monthly_posts.png"):
        """
        Построение графика количества публикаций по месяцам
        :param year: Год, за который строится график
        :param filename: Имя файла для сохранения графика
        """
        if not self.university_stats:
            print("Нет данных для построения графика")
            return
        
        plt.figure(figsize=(12, 7))
        sns.set_style("whitegrid")
        
        # Словарь для хранения данных по месяцам для каждого университета
        monthly_data = {}
        
        # Для каждого университета подготавливаем данные
        for university, stats in self.university_stats.items():
            monthly_data[university] = [0] * 12  # Создаем список из 12 нулей для каждого месяца
            
            # Подсчитываем публикации по месяцам
            for post in stats['posts_data']:
                post_date = post['date']
                if post_date.year == year:
                    month_idx = post_date.month - 1  # Индексы от 0 до 11
                    monthly_data[university][month_idx] += 1
        
        # Получаем список названий месяцев
        months = [calendar.month_name[i+1] for i in range(12)]
        
        # Создаем метки для оси X
        x = list(range(12))
        
        # Строим график для каждого университета
        for university, counts in monthly_data.items():
            plt.plot(x, counts, marker='o', linestyle='-', label=university)
        
        # Настраиваем оси и заголовок
        plt.title(f'Количество публикаций по месяцам ({year} год)', fontsize=16)
        plt.xlabel('Месяц', fontsize=14)
        plt.ylabel('Количество публикаций', fontsize=14)
        plt.xticks(x, months, rotation=45)
        plt.legend()
        plt.tight_layout()
        
        # Сохраняем график
        plt.savefig(filename)
        print(f"\nГрафик сохранен в файл: {filename}")
        
        # Показываем график
        plt.show()
    
    def save_to_excel(self, filename='university_mentions.xlsx'):
        """
        Сохранение собранных данных в Excel файл
        :param filename: Имя выходного файла
        """
        if not self.data:
            print("Нет данных для сохранения")
            return
        
        df = pd.DataFrame(self.data)
        
        # Добавляем статистику
        stats = {
            'total_posts': len(self.data),
            'unique_authors': len(self.unique_authors)
        }
        
        # Группировка по университетам для Excel
        university_stats_df = df.groupby('university').agg({
            'post_id': 'count',
            'author_id': 'nunique',
            'likes': 'sum',
            'views': 'sum',
            'reposts': 'sum',
            'comments': 'sum'
        }).reset_index()
        
        university_stats_df.columns = [
            'Университет', 
            'Количество публикаций', 
            'Количество авторов', 
            'Всего лайков', 
            'Всего просмотров', 
            'Всего репостов', 
            'Всего комментариев'
        ]
        
        # Создаем объект writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Сохраняем статистику
            pd.DataFrame([stats]).to_excel(writer, sheet_name='Общая статистика', index=False)
            university_stats_df.to_excel(writer, sheet_name='Статистика по университетам', index=False)
            
            # Сохраняем полные данные
            df_for_export = df[['university', 'date', 'text', 'likes', 'views', 'reposts', 'comments', 'post_url']]
            df_for_export.columns = [
                'Университет', 
                'Дата публикации', 
                'Текст публикации', 
                'Лайки', 
                'Просмотры', 
                'Репосты', 
                'Комментарии',
                'Ссылка на публикацию'
            ]
            df_for_export.to_excel(writer, sheet_name='Публикации', index=False)
            
            # Добавляем лист с помесячной статистикой
            self.save_monthly_stats_to_excel(writer, year=2024)
        
        print(f"\nДанные сохранены в файл: {filename}")
    
    def save_monthly_stats_to_excel(self, writer, year=2024):
        """
        Сохранение статистики по месяцам в Excel
        :param writer: Excel writer объект
        :param year: Год для статистики
        """
        # Словарь для хранения данных по месяцам для каждого университета
        monthly_data = {}
        
        # Для каждого университета подготавливаем данные
        for university, stats in self.university_stats.items():
            monthly_data[university] = [0] * 12  # Создаем список из 12 нулей для каждого месяца
            
            # Подсчитываем публикации по месяцам
            for post in stats['posts_data']:
                post_date = post['date']
                if post_date.year == year:
                    month_idx = post_date.month - 1  # Индексы от 0 до 11
                    monthly_data[university][month_idx] += 1
        
        # Получаем список названий месяцев
        months = [calendar.month_name[i+1] for i in range(12)]
        
        # Создаем DataFrame для сохранения
        monthly_df = pd.DataFrame(columns=['Университет'] + months)
        
        # Заполняем данные
        for university, counts in monthly_data.items():
            row_data = {'Университет': university}
            for i, month in enumerate(months):
                row_data[month] = counts[i]
            monthly_df = pd.concat([monthly_df, pd.DataFrame([row_data])], ignore_index=True)
        
        # Сохраняем в Excel
        monthly_df.to_excel(writer, sheet_name='Статистика по месяцам', index=False)

    def print_overall_stats(self):
        """
        Вывод общей статистики по всем университетам
        """
        print("\n" + "*" * 60)
        print(f"ОБЩАЯ СТАТИСТИКА ПО ВСЕМ УНИВЕРСИТЕТАМ")
        print("*" * 60)
        print(f"Общее количество публикаций: {len(self.data)}")
        print(f"Общее количество уникальных авторов: {len(self.unique_authors)}")
        print("*" * 60)

if __name__ == "__main__":
    # Получаем токен из переменной окружения или запрашиваем у пользователя
    config = configparser.ConfigParser()
    config.read('config.ini')
    vk_token = config['vk']['access_token']
    
    # Создаем экземпляр сборщика данных
    collector = VKUniversityMentionsCollector(vk_token)
    
    # Список университетов для поиска
    universities = ["СПбГУ", "МГУ"]
    
    # Собираем данные за 2024 год
    collector.collect_data(universities, year=2024)
    
    # Выводим общую статистику
    collector.print_overall_stats()
    
    # Строим график помесячно
    collector.plot_monthly_posts(year=2024, filename="университеты_публикации_по_месяцам_2024.png")
    
    # Сохраняем данные в Excel файл
    collector.save_to_excel("университеты_упоминания_2024.xlsx")