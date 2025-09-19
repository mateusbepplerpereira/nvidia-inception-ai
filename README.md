# NVIDIA Inception AI - Startup Discovery System

Sistema inteligente para descoberta e análise de startups de IA na América Latina para o programa NVIDIA Inception.

## 🎯 Objetivo

Automatizar a descoberta, análise e priorização de startups de IA que receberam investimento de Venture Capital, otimizando o processo de seleção para o programa NVIDIA Inception.

## 🚀 Tecnologias

- **Backend**: FastAPI (Python 3.11)
- **AI**: CrewAI + OpenAI GPT-4o-mini
- **Database**: PostgreSQL
- **Container**: Docker & Docker Compose

## 📋 Requisitos

- Docker e Docker Compose
- Chave de API da OpenAI
- Python 3.11+ (para desenvolvimento local)

## ⚙️ Configuração

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

4. Acesse a API:
- Documentação: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 🤖 Agentes de IA

O sistema utiliza 4 agentes especializados via CrewAI:

1. **Discovery Agent**: Busca startups com funding de VCs
2. **Enrichment Agent**: Coleta informações detalhadas
3. **CTO Finder**: Localiza lideranças técnicas
4. **Analysis Agent**: Avalia e prioriza startups

## 📊 Endpoints Principais

- `POST /api/agents/discover` - Descobrir startups
- `GET /api/startups` - Listar startups
- `GET /api/analysis/dashboard` - Dashboard com insights
- `GET /api/analysis/opportunities` - Startups prioritárias

## 💡 Otimizações

- **Economia de Tokens**: Max 1500 tokens por request
- **Iterações Limitadas**: 1-2 por agente
- **Processamento Sequencial**: Reduz chamadas paralelas
- **Memória CrewAI**: Compartilhamento de contexto

## 📁 Estrutura

```
backend/
├── agents/          # Agentes CrewAI
├── app/            # Rotas FastAPI
├── database/       # Modelos e conexão
├── services/       # Lógica de negócio
└── schemas/        # Validação Pydantic
```

## 🎯 Critérios de Priorização

- Alinhamento tecnológico com NVIDIA (GPU/AI)
- Oportunidade de mercado
- Força da equipe técnica
- Validação por Venture Capital

## 📝 Documentação

Veja [CLAUDE.md](CLAUDE.md) para documentação técnica detalhada.