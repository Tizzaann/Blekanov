import time
import pickle
from typing import Dict, List, Union
import argparse

class IndexSearcher:
    """
    Класс для поиска по предварительно созданному инвертированному индексу.
    """
    
    def __init__(self, index_file: str = 'index.pkl'):
        self.index_file = index_file
        self.index_data = None

    def load_index(self):
        with open(self.index_file, 'rb') as f:
            self.index_data = pickle.load(f)

    def search(self, query: str, compressed: bool = True) -> Dict[str, Union[List[int], float]]:
        if self.index_data is None:
            self.load_index()
            
        start_time = time.time()
        
        if compressed:
            results = self.index_data['compressed'].get(query, [])
        else:
            results = self.index_data['uncompressed'].get(query, [])
            
        search_time = time.time() - start_time
        
        return {
            'results': results,
            'time_sec': search_time,
            'count': len(results)
        }

    def evaluate(self, query: str) -> Dict[str, Union[float, int]]:
        if self.index_data is None:
            self.load_index()
            
        uncompressed_search = self.search(query, compressed=False)
        compressed_search = self.search(query, compressed=True)
        
        # Расчет размеров
        uncompressed_size = sum(len(pickle.dumps(doc_ids)) for doc_ids in self.index_data['uncompressed'].values())
        compressed_bits = sum(len(code) for codes in self.index_data['compressed'].values() for code in codes)
        compressed_size = compressed_bits / 8
        
        return {
            'uncompressed_size_kb': uncompressed_size / 1024,
            'compressed_size_kb': compressed_size / 1024,
            'compression_ratio': compressed_size / uncompressed_size,
            'uncompressed_search_time': uncompressed_search['time_sec'],
            'compressed_search_time': compressed_search['time_sec'],
            'results_count': uncompressed_search['count']
        }

def main():
    parser = argparse.ArgumentParser(description='Поиск по инвертированному индексу')
    parser.add_argument('query', type=str, help='Поисковый запрос')
    parser.add_argument('--index', type=str, default='index.pkl', help='Путь к файлу индекса')
    args = parser.parse_args()
    
    searcher = IndexSearcher(index_file=args.index)
    metrics = searcher.evaluate(args.query)
    
    print(f"Размер индекса без сжатия: {metrics['uncompressed_size_kb']:.2f} KB")
    print(f"Размер индекса со сжатием: {metrics['compressed_size_kb']:.2f} KB")
    print(f"Коэффициент сжатия: {metrics['compression_ratio']:.2f}x")
    print(f"Время поиска без сжатия: {metrics['uncompressed_search_time']:.6f} сек")
    print(f"Время поиска со сжатием: {metrics['compressed_search_time']:.6f} сек")
    print(f"Найдено результатов: {metrics['results_count']}")

if __name__ == '__main__':
    main()