# Como rodar o GlicoTrack localmente

## Pré-requisitos
- Python 3.11+ instalado
- Arquivo `.env` configurado com as chaves do Supabase

## Comando para iniciar o app

Abra o terminal na pasta do projeto (acima de `glicotrack/`) e execute:

```
cd glicotrack
venv\Scripts\uvicorn app.main:app --reload
```

Depois acesse **http://localhost:8000** no navegador.

## Observações
- O app fica disponível apenas enquanto o comando estiver rodando
- O `--reload` faz o servidor reiniciar automaticamente ao salvar arquivos
- Para parar o servidor, pressione `Ctrl+C` no terminal
