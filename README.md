# NVIDIA Inception AI - Startup Discovery System

Sistema inteligente para descoberta e análise de startups de IA na América Latina para o programa NVIDIA Inception.

## Objetivo

Automatizar a descoberta, validação e análise de startups de IA que receberam investimento de Venture Capital, utilizando um pipeline orquestrado de agentes para garantir qualidade e precisão dos dados.

## Tecnologias

- **Backend**: FastAPI (Python 3.11)
- **Orquestração**: LangGraph StateGraph
- **AI**: OpenAI GPT-4o-mini (direto via API)
- **Database**: PostgreSQL
- **Container**: Docker & Docker Compose

## Requisitos

- Docker e Docker Compose
- Chave de API da OpenAI
- Python 3.11+ (para desenvolvimento local)

## Configuração

1. Clone o repositório
2. Configure o arquivo `.env`:
```bash
cd backend
cp .env.example .env
# Edite o .env com sua chave OpenAI
```

3. Inicie os serviços:
```bash
docker-compose up -d
```

4. Acesse os serviços:
- **API**: http://localhost:8000/docs (Documentação)
- **Health Check**: http://localhost:8000/health
- **Adminer** (Debug DB): http://localhost:8080

## Arquitetura do Orquestrador

O sistema utiliza **LangGraph** para orquestrar 3 agentes em pipeline sequencial:

### Pipeline de Agentes:
```
Discovery Agent → Validation Agent → Metrics Agent
```

### Fluxo Detalhado:

1. **Discovery Agent** (`_discovery_agent`)
   - Descobre exatamente N startups (respeitando parâmetro `limit`)
   - Recebe contexto de startups já descobertas para evitar duplicatas
   - Exclui startups válidas e inválidas já processadas
   - Retorna lista de startups candidatas

2. **Validation Agent** (`_validation_agent`)
   - Valida rigorosamente cada startup:
     - **Website**: Verifica acessibilidade (HTTP 200)
     - **IA de Existência**: Confirma se empresa realmente existe
   - Startups válidas → salvos na tabela `startups`
   - Startups inválidas → salvos na tabela `invalid_startups`

3. **Metrics Agent** (`_metrics_agent`)
   - Calcula scores para cada startup válida:
     - **Market Demand Score** (0-100): Demanda do mercado e setor
     - **Technical Level Score** (0-100): Nível técnico do CTO/equipe
     - **Partnership Potential Score** (0-100): Potencial de parceria
     - **Total Score**: Média ponderada das métricas
   - Salva na tabela `startup_metrics`

### Estado Compartilhado:
```python
class OrchestrationState(TypedDict):
    # Dados de entrada
    country: str
    sector: str
    limit: int

    # Contexto para evitar duplicatas
    valid_startups: List[Dict]
    invalid_startups: List[Dict]

    # Resultados por agente
    discovered_startups: List[Dict]
    validated_startups: List[Dict]
    startup_metrics: List[Dict]

    # Metadados
    total_tokens: int
    processing_time: float
    errors: List[str]
```

## Endpoints da API

```

## Sistema de Filas Assíncronas

- **TaskManager Singleton**: Gerencia fila de processamento
- **Worker Thread**: Processa tasks em background
- **Status Tracking**: Acompanha progresso via database

## Critérios de Scoring

### Market Demand Score (40%):
- Setor em alta demanda
- Tecnologias relevantes
- Oportunidade de mercado

### Technical Level Score (30%):
- Qualificação do CTO
- Stack tecnológico
- Inovação técnica

### Partnership Potential Score (30%):
- Investimento recebido
- Qualidade dos investidores
- Potencial de parceria NVIDIA

## Fluxo de Operação

1. **Request** → Rota `/task/run` cria task assíncrona
2. **TaskManager** → Processa via `process_orchestration_task`
3. **LangGraph** → Executa pipeline Discovery → Validation → Metrics
4. **Persistência** → Salva resultados no PostgreSQL
5. **Response** → Cliente consulta status via `/tasks/{id}`
