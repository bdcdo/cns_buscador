#!/usr/bin/env python3
"""
Interface de linha de comando para o sistema de busca CNS
"""

import os
import sys
import argparse
from typing import Optional

# Adiciona o diretório atual ao path para importar search_engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search_engine import CNSSearchEngine


def print_results(results, query: str, max_snippet_length: int = 200):
    """Imprime resultados da busca formatados"""
    if not results:
        print(f"\n❌ Nenhum resultado encontrado para: '{query}'")
        print("\nDicas:")
        print("- Tente termos diferentes")
        print("- Use operadores: AND, OR, NOT")
        print("- Use aspas para frases exatas: \"termo exato\"")
        return
    
    print(f"\n🔍 Resultados para: '{query}'")
    print(f"📊 Total encontrado: {len(results)} documento(s)")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.titulo}")
        print(f"   📅 Data: {result.data_publicacao}")
        print(f"   📈 Score: {result.score:.2f}")
        print(f"   🔗 Link: {result.link}")
        
        # Snippet limitado
        snippet = result.snippet
        if len(snippet) > max_snippet_length:
            snippet = snippet[:max_snippet_length] + "..."
        
        print(f"   📄 Trecho: {snippet}")
        print("-" * 80)


def interactive_mode(engine: CNSSearchEngine):
    """Modo interativo de busca"""
    print("\n🔍 Modo Interativo - Buscador CNS")
    print("=" * 50)
    print("\nComandos disponíveis:")
    print("  - Digite sua busca normalmente")
    print("  - 'stats' - Ver estatísticas do índice")
    print("  - 'help' - Ver ajuda")
    print("  - 'quit' ou 'exit' - Sair")
    print("\nOperadores suportados:")
    print("  - AND: termo1 AND termo2")
    print("  - OR: termo1 OR termo2")
    print("  - NOT: termo1 NOT termo2")
    print("  - Frases: \"frase exata\"")
    print("\nExemplos:")
    print("  - saúde mental")
    print("  - \"saúde pública\"")
    print("  - pesquisa AND ética")
    print("  - medicamento OR remédio")
    print("  - hospital NOT privado")
    print("=" * 50)
    
    while True:
        try:
            query = input("\n🔍 Busca> ").strip()
            
            if not query:
                continue
            
            # Comandos especiais
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Até logo!")
                break
            
            elif query.lower() == 'stats':
                stats = engine.get_stats()
                print(f"\n📊 Estatísticas do Índice:")
                print(f"   📚 Total de documentos: {stats['total_documents']:,}")
                print(f"   🔤 Termos únicos: {stats['total_unique_terms']:,}")
                print(f"   💾 Tamanho do índice: {stats['index_size_mb']:.2f} MB")
                continue
            
            elif query.lower() in ['help', 'h', '?']:
                print("\n📖 Ajuda - Operadores de Busca:")
                print("   AND    - Ambos termos devem aparecer: 'saúde AND mental'")
                print("   OR     - Qualquer um dos termos: 'medicamento OR remédio'")
                print("   NOT    - Exclui termo: 'hospital NOT privado'")
                print("   \"...\" - Busca frase exata: '\"saúde pública\"'")
                print("   ()     - Agrupa termos: '(saúde OR medicina) AND mental'")
                print("\n💡 Dicas:")
                print("   - Use acentos ou não, o sistema normaliza")
                print("   - Termos muito curtos (< 3 letras) são ignorados")
                print("   - Combine operadores: 'saúde AND (mental OR psicológica)'")
                continue
            
            # Busca normal
            results = engine.search(query, max_results=20)
            print_results(results, query)
            
        except KeyboardInterrupt:
            print("\n\n👋 Até logo!")
            break
        except Exception as e:
            print(f"\n❌ Erro durante a busca: {e}")


def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description="Sistema de busca nas resoluções do CNS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s -q "saúde mental"                    # Busca simples
  %(prog)s -q "pesquisa AND ética"              # Operador AND
  %(prog)s -q "medicamento OR remédio"          # Operador OR
  %(prog)s -q "hospital NOT privado"            # Operador NOT
  %(prog)s -q '"saúde pública"'                 # Frase exata
  %(prog)s -i                                   # Modo interativo
  %(prog)s --rebuild-index                      # Reconstrói índice
        """
    )
    
    parser.add_argument(
        '-q', '--query',
        help='Consulta de busca'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Modo interativo'
    )
    
    parser.add_argument(
        '-n', '--num-results',
        type=int,
        default=10,
        help='Número máximo de resultados (padrão: 10)'
    )
    
    parser.add_argument(
        '--csv-path',
        help='Caminho para o arquivo CSV (padrão: ../cns_resolucoes_com_textos_20250818_132004.csv)'
    )
    
    parser.add_argument(
        '--rebuild-index',
        action='store_true',
        help='Reconstrói o índice do zero'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Mostra estatísticas do índice'
    )
    
    args = parser.parse_args()
    
    # Caminho padrão do CSV
    csv_path = args.csv_path or os.path.join(
        os.path.dirname(__file__), '..', 'cns_resolucoes_com_textos_20250818_132004.csv'
    )
    
    # Inicializa o motor de busca
    print("🔧 Inicializando sistema de busca...")
    engine = CNSSearchEngine()
    
    try:
        # Reconstrói índice se solicitado
        if args.rebuild_index:
            print("🔄 Reconstruindo índice...")
            engine.load_data(csv_path)
            engine.save_index()
            print("✅ Índice reconstruído com sucesso!")
            return
        
        # Tenta carregar índice existente
        if not engine.load_index():
            print("📚 Criando novo índice...")
            engine.load_data(csv_path)
            engine.save_index()
            print("✅ Índice criado com sucesso!")
        else:
            print("✅ Índice carregado!")
        
        # Mostra estatísticas se solicitado
        if args.stats:
            stats = engine.get_stats()
            print(f"\n📊 Estatísticas do Sistema:")
            print(f"   📚 Total de documentos: {stats['total_documents']:,}")
            print(f"   🔤 Termos únicos indexados: {stats['total_unique_terms']:,}")
            print(f"   💾 Tamanho do índice: {stats['index_size_mb']:.2f} MB")
            return
        
        # Modo interativo
        if args.interactive:
            interactive_mode(engine)
            return
        
        # Busca única
        if args.query:
            results = engine.search(args.query, max_results=args.num_results)
            print_results(results, args.query)
            return
        
        # Se nenhuma opção foi fornecida, entra em modo interativo
        interactive_mode(engine)
        
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo CSV não encontrado: {csv_path}")
        print("   Use --csv-path para especificar o caminho correto")
    except KeyboardInterrupt:
        print("\n👋 Operação cancelada pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()