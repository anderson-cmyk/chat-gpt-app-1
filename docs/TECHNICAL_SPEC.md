# Especificação Técnica - Questionário Operacional

## Visão Geral
MVP para coleta diária/mensal de respostas com escopo por operação/suboperação, autenticação JWT e dashboards básicos. Backend em FastAPI + SQLite/SQLModel, UI estática em HTML/JS com chamadas REST.

## Arquitetura
- **API**: FastAPI (`app/main.py`) com roteamento separado para autenticação, administração, captura de respostas e dashboards.
- **Persistência**: SQLite via SQLModel/SQLAlchemy (`app/models.py`, `app/database.py`).
- **Autenticação**: OAuth2 password flow com JWT (HS256) (`app/auth.py`). Perfis: `admin` e `user`.
- **UI**: `static/index.html` consome endpoints públicos.
- **Configuração**: variáveis via `pydantic-settings` (`app/config.py`), prefixo `SURVEY_`.

## Modelos de Dados
- `User`: `username`, `hashed_password`, `full_name`, `role`, `operation_id`, `sub_operation_id`, `is_active`.
- `Operation`: agrupador principal.
- `SubOperation`: filho de `Operation`.
- `Question`: `prompt`, `response_type` (`text`|`number`), `frequency` (`daily`|`monthly`), `monthly_day` (índice de dia útil 1..31), escopos opcionais de operação/suboperação, `is_active`.
- `Response`: `answer_value` (texto livre), `answer_date` (data de referência), `created_at`, FK para `user` e `question`.

## Regras de Agendamento
- Dias úteis: segunda a sábado (`utils.is_working_day`).
- Para perguntas mensais, `monthly_day` representa o **n-ésimo dia útil do mês** (1-indexado) calculado com `utils.working_day_index`.
- Perguntas só aparecem em `GET /questions/today` se `question_is_due` retornar verdadeiro.

## Endpoints Principais
- `POST /auth/token`: login e geração de JWT.
- `GET /auth/me`: perfil do usuário autenticado.
- `POST /admin/users`: cria usuário (admin apenas).
- `POST /admin/operations` / `POST /admin/sub-operations`: cadastros hierárquicos.
- `POST /admin/questions`: cria perguntas; valida `monthly_day` quando `frequency=monthly`.
- `GET /questions/today`: retorna perguntas do dia com eventual resposta já registrada para o usuário logado.
- `POST /responses`: cria/atualiza resposta para a data; bloqueia registros fora da janela de agendamento.
- `GET /dashboard/completion`: snapshot de completude por dia útil.
- `POST /dashboard/pivot`: exporta lista agregada (média ou soma) agrupada por data/questão/operação/suboperação/usuário.

## Fluxos
1. **Bootstrap**: executar `scripts/bootstrap_admin.py` para criar admin inicial; admins autenticam, cadastram operações, sub-operações, usuários e perguntas.
2. **Coleta diária**: usuários autenticam pela UI, consomem `GET /questions/today`, respondem via `POST /responses` (um registro por data/pergunta/usuário).
3. **Monitoramento**: admins consultam `dashboard` para ver quem respondeu e exportar métricas numéricas.

## Segurança e Boas Práticas
- `secret_key` deve ser definido via variável de ambiente `SURVEY_SECRET_KEY` em produção.
- Bcrypt para senhas (`passlib`).
- CORS liberado para MVP, restrinja em ambientes reais.
- SQLite é adequado para MVP; configure outro `database_url` para Postgres se necessário.

## Operação
- Healthcheck: `GET /health` retorna status e índice do dia útil atual.
- Logs padrão do Uvicorn; configure observabilidade externa conforme necessidade.
