import numpy as np
import time
import pickle
import argparse
from typing import Dict, List, Union

class InvertedIndex:
    """
    Класс для создания и работы с инвертированным индексом со сжатием Элиаса-дельта.
    Поддерживает создание индекса, сжатие, поиск и оценку производительности.
    """
    
    def __init__(self, data_file: str = 'vk_array.npy'):
        self.data_file = data_file
        self.data = None
        self.inverted_index = None
        self.inverted_index_compressed = None

    def load_data(self) -> np.ndarray:
        data = np.load(self.data_file, allow_pickle=True)
        self.data = np.repeat(data, 6) if len(data) < 40000 else data
        return self.data

    def create_inverted_index(self) -> Dict[str, List[int]]:
        if self.data is None:
            self.load_data()
            
        self.inverted_index = {}
        for doc_id, record in enumerate(self.data):
            words = record['text'].split()
            for word in words:
                if word not in self.inverted_index:
                    self.inverted_index[word] = []
                self.inverted_index[word].append(doc_id)
        return self.inverted_index

    @staticmethod
    def elias_gamma_encode(number: int) -> str:
        if number == 0:
            return '0'
        n = 1 + int(np.log2(number))
        binary = bin(number)[2:]
        return ('0' * (n - 1)) + binary

    @staticmethod
    def elias_delta_encode(number: int) -> str:
        if number == 0:
            return '0'
        binary = bin(number)[2:]
        gamma = InvertedIndex.elias_gamma_encode(len(binary))
        return gamma + binary[1:]

    def compress_index(self) -> Dict[str, List[str]]:
        if self.inverted_index is None:
            self.create_inverted_index()
            
        self.inverted_index_compressed = {
            word: [self.elias_delta_encode(doc_id) for doc_id in doc_ids]
            for word, doc_ids in self.inverted_index.items()
        }
        return self.inverted_index_compressed

    def calculate_sizes(self) -> Dict[str, float]:
        if self.inverted_index is None:
            self.create_inverted_index()
        if self.inverted_index_compressed is None:
            self.compress_index()
            
        # Размер несжатого индекса
        uncompressed_size = sum(len(pickle.dumps(doc_ids)) for doc_ids in self.inverted_index.values())
        
        # Размер сжатого индекса (в битах -> байтах)
        compressed_bits = sum(len(code) for codes in self.inverted_index_compressed.values() for code in codes)
        compressed_size = compressed_bits / 8
        
        return {
            'uncompressed_bytes': uncompressed_size,
            'compressed_bytes': compressed_size
        }

    def search(self, query: str, compressed: bool = True) -> Dict[str, Union[List[int], float]]:
        start_time = time.time()
        
        if compressed:
            results = self.inverted_index_compressed.get(query, [])
        else:
            results = self.inverted_index.get(query, [])
            
        search_time = time.time() - start_time
        
        return {
            'results': results,
            'time_sec': search_time,
            'count': len(results)
        }

    def evaluate(self, query: str) -> Dict[str, Union[float, int]]:
        sizes = self.calculate_sizes()
        uncompressed_search = self.search(query, compressed=False)
        compressed_search = self.search(query, compressed=True)
        
        return {
            'uncompressed_size_kb': sizes['uncompressed_bytes'] / 1024,
            'compressed_size_kb': sizes['compressed_bytes'] / 1024,
            'compression_ratio': sizes['compressed_bytes'] / sizes['uncompressed_bytes'],
            'uncompressed_search_time': uncompressed_search['time_sec'],
            'compressed_search_time': compressed_search['time_sec'],
            'results_count': uncompressed_search['count']
        }


def main():
    parser = argparse.ArgumentParser(description='Инвертированный индекс со сжатием Элиаса-дельта')
    parser.add_argument('query', type=str, help='Поисковый запрос (например, "ректор")')
    parser.add_argument('--data', type=str, default='vk_array.npy', help='Путь к файлу данных (по умолчанию: vk_array.npy)')
    args = parser.parse_args()
    
    # Инициализация и оценка
    index = InvertedIndex(data_file=args.data)
    metrics = index.evaluate(args.query)
    
    # Вывод результатов
    print(f"Размер индекса без сжатия: {metrics['uncompressed_size_kb']:.2f} KB")
    print(f"Размер индекса со сжатием: {metrics['compressed_size_kb']:.2f} KB")
    print(f"Коэффициент сжатия: {metrics['compression_ratio']:.2f}x")
    print(f"Время поиска без сжатия: {metrics['uncompressed_search_time']:.6f} сек")
    print(f"Время поиска со сжатием: {metrics['compressed_search_time']:.6f} сек")
    print(f"Найдено результатов: {metrics['results_count']}")


if __name__ == '__main__':
    main()