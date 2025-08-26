from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import sys
import pandas as pd
import io
from pathlib import Path

# Adiciona o diretório atual ao path para importar search_engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search_engine import CNSSearchEngine

app = FastAPI(
    title="CNS Buscador API",
    description="Sistema de busca nas resoluções do Conselho Nacional de Saúde",
    version="1.0.0"
)

# Configura templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")

# Inicializa o motor de busca
search_engine = CNSSearchEngine()

# Carrega o índice ou cria um novo
csv_path = os.path.join(os.path.dirname(__file__), 'cns_resolucoes_com_textos_20250826_150444.csv')
if not search_engine.load_index():
    print("Criando novo índice...")
    if os.path.exists(csv_path):
        search_engine.load_data(csv_path)
        search_engine.save_index()
    else:
        print(f"Arquivo CSV não encontrado: {csv_path}")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Página principal do buscador web"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/search")
async def search(
    q: str = Query(..., description="Termo de busca"),
    page: int = Query(1, ge=1, description="Número da página (mínimo 1)"),
    per_page: int = Query(25, ge=1, le=100, description="Resultados por página (1-100)")
):
    """
    Endpoint de busca com paginação
    
    - **q**: Termo de busca (obrigatório)
    - **page**: Número da página (padrão: 1)
    - **per_page**: Resultados por página (padrão: 25, máximo: 100)
    
    Suporte a operadores booleanos:
    - AND, OR, NOT
    - Frases entre aspas: "frase exata"
    """
    query = q.strip()
    if not query:
        return {
            'results': [], 
            'query': '', 
            'total': 0, 
            'page': page, 
            'per_page': per_page, 
            'total_pages': 0,
            'has_next': False,
            'has_prev': False
        }
    
    try:
        # Busca todos os resultados para calcular o total
        all_results = search_engine.search(query, max_results=10000)
        total_results = len(all_results)
        total_pages = (total_results + per_page - 1) // per_page
        
        # Calcula índices para paginação
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = all_results[start_idx:end_idx]
        
        # Converte resultados para formato JSON
        results_json = []
        for result in page_results:
            results_json.append({
                'id': result.id,
                'titulo': result.titulo,
                'score': round(result.score, 2),
                'snippet': result.snippet,
                'data_publicacao': result.data_publicacao,
                'link': result.link
            })
        
        return {
            'results': results_json,
            'query': query,
            'total': total_results,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def stats():
    """Estatísticas do índice de busca"""
    try:
        return search_engine.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_csv")
async def download_csv(q: str = Query(..., description="Termo de busca")):
    """
    Download de TODOS os resultados em formato CSV
    
    - **q**: Termo de busca (obrigatório)
    """
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query não fornecida")
    
    try:
        # Busca TODOS os resultados (sem limite)
        results = search_engine.search(query, max_results=10000)
        
        if not results:
            raise HTTPException(status_code=404, detail="Nenhum resultado encontrado")
        
        # Converte resultados para DataFrame
        data = []
        for result in results:
            data.append({
                'Título': result.titulo,
                'Data de Publicação': result.data_publicacao,
                'Link': result.link,
                'Score': result.score,
                'Trecho': result.snippet
            })
        
        df = pd.DataFrame(data)
        
        # Cria CSV em memória
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        # Nome do arquivo baseado na query
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '_')).strip()[:30]
        safe_query = safe_query.replace(' ', '_')
        filename = f"resultados_busca_{safe_query}.csv"
        
        return Response(
            content=output.getvalue(),
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/csv; charset=utf-8-sig'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Cria diretório de templates se não existir
    templates_dir = Path("templates")
    if not templates_dir.exists():
        templates_dir.mkdir()
    
    print("Iniciando servidor FastAPI...")
    print("Interface web: http://localhost:8000")
    print("Documentação da API: http://localhost:8000/docs")
    print("OpenAPI Schema: http://localhost:8000/redoc")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)