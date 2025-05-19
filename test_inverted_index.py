import unittest
from inverted_index import InvertedIndex
import numpy as np

class TestInvertedIndex(unittest.TestCase):
    
    def setUp(self):
        self.test_data = np.array([
            {'text': 'декан студент факультет'},
            {'text': 'декан преподаватель'},
            {'text': 'преподаватель экзамен'},
            {'text': ''}
        ])
        self.index = InvertedIndex()
        self.index.data = self.test_data
        self.index.create_inverted_index()

    def test_create_inverted_index(self):
        """Проверяет корректность построения инвертированного индекса."""
        expected = {
            'декан': [0, 1],
            'студент': [0],
            'факультет': [0],
            'преподаватель': [1, 2],
            'экзамен': [2]
        }
        for word, docs in expected.items():
            self.assertIn(word, self.index.inverted_index)
            self.assertEqual(self.index.inverted_index[word], docs)

    def test_search_uncompressed(self):
        """Проверяет поиск по несжатому индексу для существующего слова."""
        result = self.index.search('декан', compressed=False)
        self.assertEqual(result['results'], [0, 1])
        self.assertEqual(result['count'], 2)

    def test_search_nonexistent_word(self):
        """Проверяет поведение поиска при отсутствии слова в индексе."""
        result = self.index.search('аспирант', compressed=False)
        self.assertEqual(result['results'], [])
        self.assertEqual(result['count'], 0)

    def test_elias_delta_encode(self):
        """Проверяет корректность кодирования Элиаса-дельта для малых чисел."""
        self.assertEqual(self.index.elias_delta_encode(0), '0')
        self.assertEqual(self.index.elias_delta_encode(1), '1')
        self.assertEqual(self.index.elias_delta_encode(2), '0100')
        self.assertEqual(self.index.elias_delta_encode(3), '0101')
        self.assertEqual(self.index.elias_delta_encode(4), '01100')
        self.assertEqual(self.index.elias_delta_encode(5), '01101')

    def test_compress_index(self):
        """Проверяет, что индекс корректно сжимается строками из 0 и 1."""
        compressed = self.index.compress_index()
        self.assertIn('декан', compressed)
        self.assertTrue(all(isinstance(code, str) for code in compressed['декан']))

    def test_calculate_sizes(self):
        """Проверяет, что рассчитываются размеры сжатого и несжатого индексов."""
        self.index.compress_index()
        sizes = self.index.calculate_sizes()
        self.assertIn('uncompressed_bytes', sizes)
        self.assertIn('compressed_bytes', sizes)
        self.assertGreater(sizes['uncompressed_bytes'], 0)
        self.assertGreater(sizes['compressed_bytes'], 0)

    def test_evaluate(self):
        """Проверяет корректность метрик: время, размер, количество результатов."""
        result = self.index.evaluate('декан')
        self.assertIn('uncompressed_size_kb', result)
        self.assertIn('compressed_size_kb', result)
        self.assertIn('compression_ratio', result)
        self.assertEqual(result['results_count'], 2)
        self.assertGreaterEqual(result['uncompressed_search_time'], 0.0)
        self.assertGreaterEqual(result['compressed_search_time'], 0.0)


if __name__ == '__main__':
    unittest.main()
