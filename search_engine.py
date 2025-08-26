import pandas as pd
import re
import pickle
import os
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import unicodedata


@dataclass
class SearchResult:
    id: int
    titulo: str
    score: float
    snippet: str
    data_publicacao: str
    link: str


class TextProcessor:
    """Processa textos para indexação e busca"""
    
    def __init__(self):
        self.stopwords = {
            'a', 'o', 'e', 'de', 'da', 'do', 'das', 'dos', 'em', 'para', 'por', 'com', 'no', 'na',
            'nos', 'nas', 'um', 'uma', 'uns', 'umas', 'se', 'que', 'quando', 'onde', 'como', 'mais',
            'muito', 'mas', 'ou', 'pelo', 'pela', 'pelos', 'pelas', 'ao', 'aos', 'às', 'ser', 'estar',
            'ter', 'haver', 'seu', 'sua', 'seus', 'suas', 'meu', 'minha', 'meus', 'minhas', 'nosso',
            'nossa', 'nossos', 'nossas', 'ele', 'ela', 'eles', 'elas', 'este', 'esta', 'estes',
            'estas', 'esse', 'essa', 'esses', 'essas', 'aquele', 'aquela', 'aqueles', 'aquelas',
            'foi', 'é', 'são', 'foram', 'sendo', 'sido'
        }
    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto removendo acentos e caracteres especiais"""
        if pd.isna(text):
            return ""
        
        text = str(text).lower()
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokeniza texto em palavras"""
        normalized = self.normalize_text(text)
        tokens = normalized.split()
        return [token for token in tokens if len(token) > 2 and token not in self.stopwords]
    
    def extract_snippet(self, text: str, query_terms: List[str], max_length: int = 200) -> str:
        """Extrai snippet relevante do texto"""
        if not query_terms or pd.isna(text):
            return text[:max_length] + "..." if len(str(text)) > max_length else str(text)
        
        text_lower = text.lower()
        best_position = 0
        max_matches = 0
        
        # Encontra a posição com mais termos de busca próximos
        for i in range(0, len(text) - max_length, 20):
            snippet_text = text[i:i + max_length]
            snippet_tokens = set(self.tokenize(snippet_text))
            matches = sum(1 for term in query_terms if term.lower() in snippet_tokens)
            if matches > max_matches:
                max_matches = matches
                best_position = i
        
        snippet = text[best_position:best_position + max_length]
        if best_position > 0:
            snippet = "..." + snippet
        if best_position + max_length < len(text):
            snippet = snippet + "..."
        
        return snippet


class InvertedIndex:
    """Índice invertido para busca eficiente"""
    
    def __init__(self):
        self.index = defaultdict(set)  # termo -> set de document_ids
        self.documents = {}  # document_id -> documento
        self.processor = TextProcessor()
    
    def add_document(self, doc_id: int, document: Dict):
        """Adiciona documento ao índice"""
        self.documents[doc_id] = document
        
        # Indexa título com peso maior
        if 'titulo' in document:
            title_tokens = self.processor.tokenize(document['titulo'])
            for token in title_tokens:
                self.index[token].add(doc_id)
                self.index[f"title:{token}"].add(doc_id)  # tokens do título com prefixo
        
        # Indexa texto do PDF
        if 'texto' in document and not pd.isna(document['texto']):
            text_tokens = self.processor.tokenize(document['texto'])
            for token in text_tokens:
                self.index[token].add(doc_id)
    
    def search(self, query: str) -> List[int]:
        """Busca documentos que correspondem à query"""
        return self._parse_boolean_query(query)

    def _parse_boolean_query(self, query: str) -> List[int]:
        """Analisa query com operadores booleanos e parênteses."""
        query = query.strip()
        
        # Suporte para frases entre aspas
        phrase_pattern = r'"([^"]+)"'
        phrases = re.findall(phrase_pattern, query)
        
        # Substitui frases por placeholders para não interferir com a lógica de parênteses
        placeholder_offset = 1000 # Evita colisão com placeholders de parênteses
        for i, phrase in enumerate(phrases):
            query = query.replace(f'"{phrase}"', f'__PHRASE__{i+placeholder_offset}__', 1)

        sub_results = {}
        # Armazena resultados de frases primeiro
        for i, phrase in enumerate(phrases):
            placeholder = f'__PHRASE__{i+placeholder_offset}__'
            sub_results[placeholder] = set(self._search_phrase(phrase))

        # Processa parênteses iterativamente, dos mais internos para os mais externos
        placeholder_id = 0
        while '(' in query:
            match = re.search(r'\(([^()]+)\)', query)
            if not match:
                # Se não houver mais parênteses simples, pode haver um erro de aninhamento
                # ou a query está mal formada. Retornamos um resultado vazio para segurança.
                return [] 

            sub_query = match.group(1)
            placeholder = f'__SUB__{placeholder_id}__'
            
            # Avalia a subquery simples
            result_set = self._evaluate_simple_query(sub_query, sub_results)
            sub_results[placeholder] = result_set
            
            # Substitui a subquery pelo placeholder
            query = query.replace(match.group(0), placeholder, 1)
            placeholder_id += 1

        # Avalia a query final (agora plana)
        final_result_set = self._evaluate_simple_query(query, sub_results)
        return list(final_result_set)

    def _evaluate_simple_query(self, query: str, sub_results: Dict[str, Set[int]]) -> Set[int]:
        """Avalia uma query booleana 'plana' (sem parênteses)."""
        # Parse operadores OR
        or_parts = [part.strip() for part in query.split(' OR ')]
        
        final_result = set()
        
        for or_part in or_parts:
            if not or_part:
                continue
            
            # Parse operadores AND e NOT para esta parte
            and_result = self._parse_and_not(or_part, sub_results)
            final_result.update(and_result)
        
        return final_result

    def _parse_and_not(self, query_part: str, sub_results: Dict[str, Set[int]]) -> Set[int]:
        """Analisa parte da query com AND e NOT"""
        parts = query_part.split()
        positive_terms = []
        negative_terms = []
        
        i = 0
        while i < len(parts):
            if parts[i] == 'NOT' and i + 1 < len(parts):
                negative_terms.append(parts[i + 1])
                i += 2
            elif parts[i] == 'AND':
                i += 1
            else:
                positive_terms.append(parts[i])
                i += 1
        
        if not positive_terms:
            return set()
        
        # Busca termos positivos (AND implícito)
        result_sets = []
        for term in positive_terms:
            if term.startswith('__SUB__') or term.startswith('__PHRASE__'):
                term_results = sub_results.get(term, set())
            else:
                term_results = set(self._search_term(term))
            
            result_sets.append(term_results)
        
        # Interseção de todos os conjuntos positivos
        if not result_sets:
            return set()
            
        result = result_sets[0].copy()
        for result_set in result_sets[1:]:
            result.intersection_update(result_set)
        
        # Remove termos negativos
        for negative_term in negative_terms:
            if negative_term.startswith('__SUB__') or negative_term.startswith('__PHRASE__'):
                negative_results = sub_results.get(negative_term, set())
            else:
                negative_results = set(self._search_term(negative_term))
            result.difference_update(negative_results)
        
        return result

    def _search_term(self, term: str) -> List[int]:
        """Busca um termo específico"""
        normalized_term = self.processor.normalize_text(term)
        if normalized_term in self.index:
            return list(self.index[normalized_term])
        return []
    
    def _search_phrase(self, phrase: str) -> List[int]:
        """Busca uma frase exata"""
        phrase_tokens = self.processor.tokenize(phrase)
        if not phrase_tokens:
            return []
        
        # Começa com documentos que contêm o primeiro token
        # Usamos set() para garantir que a busca inicial seja em um conjunto
        candidate_docs = set(self._search_term(phrase_tokens[0]))
        
        # Filtra documentos que realmente contêm a frase
        result_docs = []
        for doc_id in candidate_docs:
            doc = self.documents[doc_id]
            text_content = ""
            if 'titulo' in doc:
                text_content += doc['titulo'] + " "
            if 'texto' in doc and not pd.isna(doc['texto']):
                text_content += str(doc['texto'])
            
            normalized_content = self.processor.normalize_text(text_content)
            normalized_phrase = ' '.join(phrase_tokens) # Usa os tokens normalizados para a busca
            
            if normalized_phrase in normalized_content:
                result_docs.append(doc_id)
        
        return result_docs


class CNSSearchEngine:
    """Sistema de busca principal"""
    
    def __init__(self, csv_path: str = None):
        self.index = InvertedIndex()
        self.processor = TextProcessor()
        self.csv_path = csv_path
        self.index_path = 'cns_search_index.pkl'
        
    def load_data(self, csv_path: str = None):
        """Carrega dados do CSV"""
        if csv_path:
            self.csv_path = csv_path
        
        print("Carregando dados...")
        df = pd.read_csv(self.csv_path)
        print(f"Dados carregados: {len(df)} documentos")
        
        # Adiciona documentos ao índice
        print("Criando índice...")
        for idx, row in df.iterrows():
            self.index.add_document(idx, row.to_dict())
        
        print("Índice criado com sucesso!")
        return len(df)
    
    def save_index(self):
        """Salva o índice em arquivo"""
        with open(self.index_path, 'wb') as f:
            pickle.dump(self.index, f)
        print(f"Índice salvo em {self.index_path}")
    
    def load_index(self):
        """Carrega o índice de arquivo"""
        if os.path.exists(self.index_path):
            with open(self.index_path, 'rb') as f:
                self.index = pickle.load(f)
            print(f"Índice carregado de {self.index_path}")
            return True
        return False
    
    def search(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """Realiza busca e retorna resultados ordenados"""
        if not query.strip():
            return []
        
        # Busca no índice
        doc_ids = self.index.search(query)
        
        if not doc_ids:
            return []
        
        # Calcula scores e prepara resultados
        query_tokens = self.processor.tokenize(query)
        results = []
        
        for doc_id in doc_ids[:max_results]:
            doc = self.index.documents[doc_id]
            score = self._calculate_score(doc, query_tokens)
            
            snippet = self.processor.extract_snippet(
                str(doc.get('texto', '')), 
                query_tokens
            )
            
            result = SearchResult(
                id=doc_id,
                titulo=doc.get('titulo', ''),
                score=score,
                snippet=snippet,
                data_publicacao=doc.get('data_publicacao', ''),
                link=doc.get('link', '')
            )
            results.append(result)
        
        # Ordena por score decrescente
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]
    
    def _calculate_score(self, document: Dict, query_tokens: List[str]) -> float:
        """Calcula score de relevância do documento"""
        score = 0.0
        
        # Score baseado no título (peso maior)
        if 'titulo' in document:
            title_tokens = set(self.processor.tokenize(document['titulo']))
            for token in query_tokens:
                if token in title_tokens:
                    score += 3.0
        
        # Score baseado no texto do PDF
        if 'texto' in document and not pd.isna(document['texto']):
            pdf_tokens = self.processor.tokenize(str(document['texto']))
            for token in query_tokens:
                count = pdf_tokens.count(token)
                score += count * 1.0
        
        return score
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do índice"""
        return {
            'total_documents': len(self.index.documents),
            'total_unique_terms': len(self.index.index),
            'index_size_mb': len(str(self.index)) / (1024 * 1024)
        }


if __name__ == "__main__":
    # Exemplo de uso
    engine = CNSSearchEngine()
    
    # Carrega dados
    engine.load_data('/home/bdcdo/Desktop/dev/10_cns_buscador/cns_resolucoes_com_textos_20250826_150444.csv')
    
    # Salva índice
    engine.save_index()
    
    # Exemplos de busca
    queries = [
        "saúde mental",
        "saúde AND mental",
        "saúde OR medicina",
        '"saúde pública"',
        "saúde NOT privada",
        '(saúde AND mulher) OR "direitos humanos"' # Novo exemplo com parênteses
    ]
    
    for query in queries:
        print(f"\nBusca: '{query}'")
        results = engine.search(query, max_results=5)
        print(f"Encontrados: {len(results)} resultados")
        
        for result in results:
            print(f"- {result.titulo} (Score: {result.score:.2f})")
            print(f"  {result.snippet[:100]}...")
