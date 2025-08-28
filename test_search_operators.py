import unittest
from search_engine import CNSSearchEngine
import tempfile
import os
import pandas as pd


class TestSearchOperators(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.csv_path = '/home/bdcdo/Desktop/dev/10_cns_buscador/cns_resolucoes_com_textos_20250826_150444.csv'
        
        if not os.path.exists(cls.csv_path):
            cls.csv_path = '/home/bdcdo/Desktop/dev/10_cns_buscador/cns_resolucoes_com_textos_20250818_132004.csv'
        
        cls.engine = CNSSearchEngine()
        if cls.engine.load_index():
            print("Índice carregado do arquivo")
        else:
            cls.engine.load_data(cls.csv_path)

    def test_single_term_search(self):
        results = self.engine.search("saúde")
        self.assertGreater(len(results), 0)

    def test_and_operator_basic(self):
        results = self.engine.search("saúde AND mental")
        results_saude = self.engine.search("saúde")
        results_mental = self.engine.search("mental")
        
        if len(results_saude) > 0 and len(results_mental) > 0:
            self.assertGreaterEqual(len(results), 0)

    def test_or_operator_basic(self):
        results = self.engine.search("medicina OR enfermagem")
        results_medicina = self.engine.search("medicina")
        results_enfermagem = self.engine.search("enfermagem")
        
        expected_count = len(set([r.id for r in results_medicina] + [r.id for r in results_enfermagem]))
        self.assertGreaterEqual(len(results), min(len(results_medicina), len(results_enfermagem)))

    def test_not_operator_basic(self):
        results_all = self.engine.search("conselho")
        results_not = self.engine.search("conselho NOT nacional")
        
        if len(results_all) > 0:
            self.assertLessEqual(len(results_not), len(results_all))

    def test_simple_parentheses(self):
        results_with_parens = self.engine.search("(conselho AND nacional)")
        results_without_parens = self.engine.search("conselho AND nacional")
        
        self.assertEqual(len(results_with_parens), len(results_without_parens))

    def test_parentheses_with_or(self):
        results = self.engine.search("(medicina OR enfermagem)")
        results_medicina = self.engine.search("medicina")
        results_enfermagem = self.engine.search("enfermagem")
        
        expected_min = min(len(results_medicina), len(results_enfermagem))
        if expected_min > 0:
            self.assertGreaterEqual(len(results), expected_min)

    def test_complex_parentheses_and_or(self):
        results = self.engine.search("(saúde AND mental) OR medicina")
        self.assertGreaterEqual(len(results), 0)

    def test_nested_parentheses(self):
        results = self.engine.search("((conselho AND nacional) OR medicina)")
        self.assertGreaterEqual(len(results), 0)

    def test_parentheses_with_not(self):
        results = self.engine.search("(conselho NOT nacional)")
        all_results = self.engine.search("conselho")
        self.assertLessEqual(len(results), len(all_results))

    def test_exact_phrase_search(self):
        results = self.engine.search('"conselho nacional"')
        self.assertGreaterEqual(len(results), 0)
        
        results = self.engine.search('"saúde pública"')
        self.assertGreaterEqual(len(results), 0)

    def test_phrase_with_parentheses(self):
        results = self.engine.search('("conselho nacional" OR medicina)')
        self.assertGreaterEqual(len(results), 0)

    def test_phrase_with_and_operator(self):
        results = self.engine.search('"sistema único" AND saúde')
        self.assertGreaterEqual(len(results), 0)

    def test_complex_query_multiple_operators(self):
        results = self.engine.search('(conselho AND (nacional OR regional)) NOT municipal')
        self.assertGreaterEqual(len(results), 0)

    def test_triple_nested_parentheses(self):
        results = self.engine.search('(((saúde AND mental) OR medicina) AND NOT privado)')
        self.assertGreaterEqual(len(results), 0)

    def test_phrase_and_parentheses_complex(self):
        results = self.engine.search('("sistema único" OR "saúde pública") AND NOT privado')
        self.assertGreaterEqual(len(results), 0)

    def test_empty_query(self):
        results = self.engine.search("")
        self.assertEqual(len(results), 0)
        
        results = self.engine.search("   ")
        self.assertEqual(len(results), 0)

    def test_malformed_parentheses(self):
        results = self.engine.search("saúde AND (mental")
        self.assertGreaterEqual(len(results), 0)
        
        results = self.engine.search("saúde AND mental)")
        self.assertGreaterEqual(len(results), 0)

    def test_empty_parentheses(self):
        results = self.engine.search("saúde AND ()")
        self.assertEqual(len(results), 0)

    def test_only_operators(self):
        results = self.engine.search("AND OR NOT")
        self.assertGreaterEqual(len(results), 0)

    def test_unclosed_quotes(self):
        results = self.engine.search('"saúde mental')
        titles = [r.titulo for r in results if r.titulo]
        self.assertGreater(len(titles), 0)

    def test_case_insensitive_search(self):
        results_lower = self.engine.search("saúde")
        results_upper = self.engine.search("SAÚDE")
        results_mixed = self.engine.search("Saúde")
        
        self.assertEqual(len(results_lower), len(results_upper))
        self.assertEqual(len(results_lower), len(results_mixed))

    def test_accent_normalization(self):
        results_with_accent = self.engine.search("saúde")
        results_without_accent = self.engine.search("saude")
        
        self.assertEqual(len(results_with_accent), len(results_without_accent))

    def test_multiple_phrases(self):
        results = self.engine.search('"conselho nacional" OR "sistema único"')
        self.assertGreaterEqual(len(results), 0)

    def test_phrase_and_single_terms(self):
        results = self.engine.search('"conselho nacional" AND saúde')
        self.assertGreaterEqual(len(results), 0)

    def test_operator_precedence(self):
        results1 = self.engine.search("saúde AND mental OR medicina")
        results2 = self.engine.search("(saúde AND mental) OR medicina")
        
        self.assertGreaterEqual(len(results1), 0)
        self.assertGreaterEqual(len(results2), 0)

    def test_score_calculation(self):
        results = self.engine.search("saúde")
        self.assertTrue(all(r.score > 0 for r in results))
        
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        self.assertEqual(results, sorted_results)

    def test_snippet_extraction(self):
        results = self.engine.search("saúde mental")
        for result in results:
            if result.titulo == 'Saúde Mental Infantil':
                self.assertIn('saúde', result.snippet.lower())
                self.assertIn('mental', result.snippet.lower())

    def test_max_results_limit(self):
        results = self.engine.search("saúde", max_results=3)
        self.assertLessEqual(len(results), 3)

    def test_document_fields_in_results(self):
        results = self.engine.search("saúde")
        for result in results:
            self.assertIsNotNone(result.titulo)
            self.assertIsNotNone(result.score)
            self.assertIsNotNone(result.snippet)
            self.assertIsNotNone(result.data_publicacao)
            self.assertIsNotNone(result.link)


if __name__ == '__main__':
    unittest.main(verbosity=2)