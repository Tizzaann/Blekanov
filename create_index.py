import numpy as np
import pickle
from typing import Dict, List
import argparse

class IndexCreator:
    """
    Класс для создания и сжатия инвертированного индекса.
    Сохраняет индекс в файл для последующего использования.
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
        gamma = IndexCreator.elias_gamma_encode(len(binary))
        return gamma + binary[1:]

    def compress_index(self) -> Dict[str, List[str]]:
        if self.inverted_index is None:
            self.create_inverted_index()
            
        self.inverted_index_compressed = {
            word: [self.elias_delta_encode(doc_id) for doc_id in doc_ids]
            for word, doc_ids in self.inverted_index.items()
        }
        return self.inverted_index_compressed

    def save_index(self, output_file: str = 'index.pkl'):
        if self.inverted_index_compressed is None:
            self.compress_index()
            
        with open(output_file, 'wb') as f:
            pickle.dump({
                'compressed': self.inverted_index_compressed,
                'uncompressed': self.inverted_index
            }, f)

def main():
    parser = argparse.ArgumentParser(description='Создание инвертированного индекса со сжатием')
    parser.add_argument('--data', type=str, default='vk_array.npy', help='Путь к файлу данных')
    parser.add_argument('--output', type=str, default='index.pkl', help='Путь для сохранения индекса')
    args = parser.parse_args()
    
    creator = IndexCreator(data_file=args.data)
    creator.save_index(output_file=args.output)
    print(f"Индекс успешно создан и сохранен в {args.output}")

if __name__ == '__main__':
    main()