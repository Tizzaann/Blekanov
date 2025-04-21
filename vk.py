import vk_api
import pandas as pd
from datetime import datetime, timedelta
import time
import calendar
import configparser
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

class VKUniversityMentionsCollector:
    def __init__(self, access_token):
        self.access_token = access_token
        self.vk_session = vk_api.VkApi(token=access_token)
        self.vk = self.vk_session.get_api()
        self.data = []
        self.unique_authors = set()
        self.university_stats = {}

    def search_posts(self, query, start_time, end_time, count=200):
        posts_found = []
        start_from = None

        while True:
            params = {
                'q': query,
                'start_time': start_time,
                'end_time': end_time,
                'count': count,
            }
            if start_from:
                params['start_from'] = start_from

            try:
                response = self.vk.newsfeed.search(**params)
            except vk_api.exceptions.ApiError as e:
                print(f"API Error: {e}")
                break

            items = response.get('items', [])
            if not items:
                break

            posts_found.extend(items)
            start_from = response.get('next_from')
            if not start_from:
                break

            time.sleep(0.34)

        return posts_found

    def collect_data(self, universities):
        """
        Сбор данных о публикациях за последние 5 дней
        """
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=5)

        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        print(f"Сбор данных за период с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}")

        for university in universities:
            print(f"\nПоиск упоминаний: {university}")
            university_posts = []
            university_authors = set()
            stats = {'likes': 0, 'views': 0, 'reposts': 0, 'comments': 0}

            posts = self.search_posts(university, start_ts, end_ts)
            print(f"  найдено {len(posts)} постов")

            for post in posts:
                dt = datetime.fromtimestamp(post.get('date', 0))
                date_str = dt.strftime('%Y-%m-%d')
                record = {
                    'university': university,
                    'post_id': post.get('id'),
                    'owner_id': post.get('owner_id'),
                    'author_id': post.get('from_id', post.get('owner_id')),
                    'date': dt,
                    'text': post.get('text', ''),
                    'likes': post.get('likes', {}).get('count', 0),
                    'views': post.get('views', {}).get('count', 0),
                    'reposts': post.get('reposts', {}).get('count', 0),
                    'comments': post.get('comments', {}).get('count', 0),
                    'post_url': f"https://vk.com/wall{post.get('owner_id')}_{post.get('id')}"
                }
                self.data.append(record)
                university_posts.append(record)
                university_authors.add(record['author_id'])
                stats['likes'] += record['likes']
                stats['views'] += record['views']
                stats['reposts'] += record['reposts']
                stats['comments'] += record['comments']

            self.university_stats[university] = {
                'posts_count': len(university_posts),
                'authors_count': len(university_authors),
                'likes_count': stats['likes'],
                'views_count': stats['views'],
                'reposts_count': stats['reposts'],
                'comments_count': stats['comments'],
                'posts_data': university_posts
            }
            self.print_university_stats(university)

    def print_university_stats(self, university):
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

    def plot_daily_posts(self, filename="daily_posts.png"):
        if not self.university_stats:
            print("Нет данных для построения графика")
            return

        plt.figure(figsize=(12, 7))
        sns.set_style("whitegrid")
        daily_data = {}

        for university, stats in self.university_stats.items():
            daily_data[university] = {}
            for post in stats['posts_data']:
                date_str = post['date'].strftime('%Y-%m-%d')
                daily_data[university][date_str] = daily_data[university].get(date_str, 0) + 1

        all_dates = sorted({d for u in daily_data.values() for d in u.keys()})
        for university, date_counts in daily_data.items():
            y = [date_counts.get(date, 0) for date in all_dates]
            plt.plot(all_dates, y, marker='o', linestyle='-', label=university)

        plt.title('Количество публикаций по дням (последние 5 дней)', fontsize=16)
        plt.xlabel('Дата', fontsize=14)
        plt.ylabel('Количество публикаций', fontsize=14)
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename)
        print(f"График сохранен в файл: {filename}")
        plt.show()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    vk_token = config['vk']['access_token']
    collector = VKUniversityMentionsCollector(vk_token)
    universities = ["СПбГУ", "МГУ"]
    collector.collect_data(universities)
    collector.plot_daily_posts(filename="университеты_по_дням.png")
