# Deploy no Fly.io

## Como fazer deploy do CNS Buscador

### Pré-requisitos
1. Instalar flyctl: `curl -L https://fly.io/install.sh | sh`
2. Criar conta no Fly.io: `flyctl auth signup`
3. Fazer login: `flyctl auth login`

### Deploy

1. **Preparar a aplicação:**
   ```bash
   # Instalar dependências localmente (opcional, para testar)
   pip install -r requirements.txt
   
   # Testar localmente
   python main.py
   # Abra http://localhost:8000 para testar
   ```

2. **Deploy no Fly.io:**
   ```bash
   # Inicializar app no Fly.io (só na primeira vez)
   flyctl launch --no-deploy
   
   # Fazer deploy
   flyctl deploy
   ```

3. **Monitorar:**
   ```bash
   # Ver logs
   flyctl logs
   
   # Ver status
   flyctl status
   
   # Abrir no navegador
   flyctl open
   ```

### Endpoints Disponíveis

Após o deploy, sua aplicação terá:

#### Interface Web (Buscador)
- `https://seu-app.fly.dev/` - Interface web amigável

#### API REST
- `https://seu-app.fly.dev/docs` - Documentação interativa da API
- `https://seu-app.fly.dev/search?q=termo&page=1&per_page=25` - Busca via API
- `https://seu-app.fly.dev/download_csv?q=termo` - Download de todos os resultados
- `https://seu-app.fly.dev/stats` - Estatísticas do índice

### Exemplos de Uso da API

```bash
# Busca simples
curl "https://seu-app.fly.dev/search?q=saude"

# Busca com paginação
curl "https://seu-app.fly.dev/search?q=saude&page=2&per_page=50"

# Busca com operadores booleanos
curl "https://seu-app.fly.dev/search?q=saude%20AND%20mental"

# Download CSV
curl -o resultados.csv "https://seu-app.fly.dev/download_csv?q=saude"

# Estatísticas
curl "https://seu-app.fly.dev/stats"
```

### Configuração

- **Memória**: 1GB (configurado no fly.toml)
- **CPU**: 1 CPU compartilhada
- **Auto-scaling**: Liga/desliga automaticamente
- **Região**: São Paulo (gru)

### Resolução de Problemas

```bash
# Se o deploy falhar
flyctl logs

# Reiniciar a aplicação
flyctl restart

# Conectar via SSH (debug)
flyctl ssh console
```