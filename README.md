# Questionário Operacional

Aplicação FastAPI + SQLite para capturar respostas diárias ou mensais de usuários por operação/suboperação e entregar dashboards de completude e pivotagem simples.

## Pré-requisitos
- Python 3.11+
- `pip` para instalar dependências

## Instalação
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Banco e usuário administrador
Crie o banco e um usuário administrador inicial:
```bash
python scripts/bootstrap_admin.py
```

## Executando a API e a UI
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
A UI simples está disponível em `http://localhost:8000/`.

## Fluxo administrativo (API)
Use um cliente REST autenticado como admin (token em `/auth/token`) para:
- Criar operações: `POST /admin/operations`
- Criar sub-operações: `POST /admin/sub-operations`
- Criar usuários: `POST /admin/users`
- Criar perguntas: `POST /admin/questions` (tipos `text` ou `number`, frequência `daily` ou `monthly` com `monthly_day`)

## Respostas do usuário
- Login via UI (ou `/auth/token`).
- `GET /questions/today` traz somente perguntas ativas agendadas para o dia útil.
- `POST /responses` registra/atualiza a resposta do dia.

## Dashboard
- `GET /dashboard/completion?date=YYYY-MM-DD` mostra quem respondeu no dia útil.
- `POST /dashboard/pivot` retorna linhas agregadas (média ou soma) para exportação.

## Teste rápido com `curl`
```bash
# healthcheck
curl http://localhost:8000/health
```

## Estrutura
- `app/` código da API (modelos, autenticação, rotas, utilidades)
- `static/` UI HTML/JS
- `scripts/` utilitários (ex: criação de admin)
- `docs/` documentação técnica adicional
