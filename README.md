# Buscador CNS - Resoluções do Conselho Nacional de Saúde

Sistema de busca otimizado para as resoluções do Conselho Nacional de Saúde, com suporte a operadores booleanos e interface web/CLI.

## 🚀 Características

- **Busca rápida**: Índice invertido para busca eficiente
- **Operadores booleanos**: AND, OR, NOT
- **Frases exatas**: Busca entre aspas
- **Interface web**: Interface moderna e responsiva
- **CLI interativo**: Terminal com comandos avançados
- **Normalização de texto**: Remove acentos e caracteres especiais
- **Snippets relevantes**: Trechos contextualizados dos resultados

## 📦 Instalação

1. **Clone ou acesse o diretório**:
```bash
cd /home/bdcdo/Desktop/dev/5_sabara-doencas-raras/v5/cns_buscador
```

2. **Crie e ative um ambiente virtual**:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

## 🔧 Uso

### Interface Web

1. **Inicie o servidor**:
```bash
python3 web_interface.py
```

2. **Acesse no navegador**:
```
http://localhost:5000
```

### Interface de Linha de Comando (CLI)

1. **Modo interativo**:
```bash
python3 cli_interface.py -i
```

2. **Busca única**:
```bash
python3 cli_interface.py -q "saúde mental"
```

3. **Ver estatísticas**:
```bash
python3 cli_interface.py --stats
```

## 🔍 Operadores de Busca

### Operadores Básicos
- **AND**: `saúde AND mental` - Ambos termos devem aparecer
- **OR**: `medicamento OR remédio` - Qualquer um dos termos
- **NOT**: `hospital NOT privado` - Exclui documentos com "privado"

### Frases Exatas
- `"saúde pública"` - Busca a frase exata

### Exemplos Avançados
```bash
# Busca simples
saúde mental

# Operadores booleanos
pesquisa AND ética
medicamento OR remédio OR fármaco
hospital NOT privado

# Frases exatas
"saúde pública"
"conselho nacional de saúde"

# Combinações
(saúde OR medicina) AND mental
"pesquisa clínica" AND NOT veterinária
```

## 🏗️ Arquitetura

### Componentes

1. **`search_engine.py`**: Motor de busca principal
   - `TextProcessor`: Normalização e tokenização
   - `InvertedIndex`: Índice invertido para busca eficiente
   - `CNSSearchEngine`: Interface principal

2. **`web_interface.py`**: Interface web Flask
   - Endpoints REST para busca
   - Interface HTML responsiva
   - Busca em tempo real

3. **`cli_interface.py`**: Interface de linha de comando
   - Modo interativo
   - Busca única
   - Comandos de administração

### Estrutura de Dados

```
📁 cns_buscador/
├── 📄 search_engine.py      # Motor de busca
├── 📄 web_interface.py      # Interface web
├── 📄 cli_interface.py      # Interface CLI
├── 📄 requirements.txt      # Dependências
├── 📄 README.md            # Este arquivo
└── 📁 templates/
    └── 📄 index.html       # Template HTML
```

## ⚡ Performance

- **Indexação**: ~518 documentos indexados
- **Busca**: < 100ms para consultas típicas
- **Memória**: ~10-50MB para o índice completo
- **Normalização**: Remove acentos, pontuação e stop words

## 🔧 Administração

### Recriar Índice
```bash
python3 cli_interface.py --rebuild-index
```

### Especificar CSV Customizado
```bash
python3 cli_interface.py --csv-path /caminho/para/arquivo.csv
```

### Ver Estatísticas Detalhadas
```bash
python3 cli_interface.py --stats
```

## 💡 Dicas de Uso

1. **Termos curtos**: Palavras com menos de 3 letras são ignoradas
2. **Acentos**: O sistema normaliza automaticamente (saúde = saude)
3. **Stop words**: Palavras muito comuns são filtradas
4. **Scoring**: Resultados são ordenados por relevância
5. **Título**: Matches no título têm peso maior

## 🐛 Solução de Problemas

### Erro: Módulo não encontrado
```bash
# Certifique-se de estar no ambiente virtual
source venv/bin/activate
pip install -r requirements.txt
```

### Erro: CSV não encontrado
```bash
# Especifique o caminho correto
python3 cli_interface.py --csv-path ../cns_resolucoes_com_textos_20250818_132004.csv
```

### Performance lenta
```bash
# Recrie o índice
python3 cli_interface.py --rebuild-index
```

## 📊 Exemplos de Consultas

```bash
# Saúde mental
python3 cli_interface.py -q "saúde mental"

# Pesquisa ética
python3 cli_interface.py -q "pesquisa AND ética"

# Medicamentos (qualquer termo)
python3 cli_interface.py -q "medicamento OR remédio OR fármaco"

# Hospitais públicos (não privados)
python3 cli_interface.py -q "hospital NOT privado"

# Frase exata
python3 cli_interface.py -q '"conselho nacional de saúde"'
```

## 🔄 Atualizações

Para atualizar o sistema com novos dados:

1. Substitua o arquivo CSV pelos dados atualizados
2. Recrie o índice: `python3 cli_interface.py --rebuild-index`
3. Reinicie o servidor web se estiver rodando

## 📝 Licença

Este projeto é de uso interno para análise das resoluções do CNS.