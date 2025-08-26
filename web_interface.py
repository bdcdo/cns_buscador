from flask import Flask, render_template, request, jsonify, Response
import os
import sys
import pandas as pd
import io

# Adiciona o diretório atual ao path para importar search_engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search_engine import CNSSearchEngine

app = Flask(__name__)

# Inicializa o motor de busca
search_engine = CNSSearchEngine()

# Carrega o índice ou cria um novo
csv_path = os.path.join(os.path.dirname(__file__), '..', 'cns_resolucoes_com_textos_20250818_132004.csv')
if not search_engine.load_index():
    print("Criando novo índice...")
    search_engine.load_data(csv_path)
    search_engine.save_index()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/search')
def search():
    """Endpoint de busca"""
    query = request.args.get('q', '').strip()
    max_results = int(request.args.get('limit', 20))
    
    if not query:
        return jsonify({'results': [], 'query': '', 'total': 0})
    
    try:
        results = search_engine.search(query, max_results=max_results)
        
        # Converte resultados para formato JSON
        results_json = []
        for result in results:
            results_json.append({
                'id': result.id,
                'titulo': result.titulo,
                'score': round(result.score, 2),
                'snippet': result.snippet,
                'data_publicacao': result.data_publicacao,
                'link': result.link
            })
        
        return jsonify({
            'results': results_json,
            'query': query,
            'total': len(results_json)
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'results': [],
            'query': query,
            'total': 0
        }), 500

@app.route('/stats')
def stats():
    """Endpoint de estatísticas"""
    try:
        stats = search_engine.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_csv')
def download_csv():
    """Endpoint para download dos resultados em CSV"""
    query = request.args.get('q', '').strip()
    max_results = int(request.args.get('limit', 100))
    
    if not query:
        return jsonify({'error': 'Query não fornecida'}), 400
    
    try:
        results = search_engine.search(query, max_results=max_results)
        
        if not results:
            return jsonify({'error': 'Nenhum resultado encontrado'}), 404
        
        # Converte resultados para DataFrame
        data = []
        for result in results:
            data.append({
                'Título': result.titulo,
                'Data de Publicação': result.data_publicacao,
                'Link': result.link,
                'Trecho': result.snippet
            })
        
        df = pd.DataFrame(data)
        
        # Cria CSV em memória
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        # Nome do arquivo baseado na query - remove caracteres problemáticos
        safe_query = query.replace(' ', '_').replace('"', '').replace("'", '').replace('/', '').replace('\\', '').replace(':', '').replace('*', '').replace('?', '').replace('<', '').replace('>', '').replace('|', '')[:30]
        filename = f"resultados_busca_{safe_query}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/csv; charset=utf-8-sig'
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Cria templates se não existir
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    print("Iniciando servidor web...")
    print("Acesse: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)