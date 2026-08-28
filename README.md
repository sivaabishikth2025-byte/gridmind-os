# GridMind OS — Autonomous AI-Powered Grid Optimization Platform

A production-grade platform for monitoring, predicting, and optimizing energy usage in real time.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Simulator  │────▶│  FastAPI     │────▶│  Next.js        │
│  (Physics)  │     │  Backend     │     │  Command Center │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         PostgreSQL      Redis       Open-Meteo
         (TimescaleDB)   (Pub/Sub)    (Weather API)
```

## Features

- **Live Grid Telemetry** — Real-time WebSocket streaming of load, solar, battery, voltage, frequency
- **AI Load Forecasting** — Gradient Boosting model with weather integration
- **Battery Dispatch Optimization** — PuLP linear programming (cost/carbon/peak objectives)
- **Anomaly Detection** — Isolation Forest with rule-based root cause analysis
- **Carbon Auditing** — Real-time Scope 1/2 emissions ledger with marginal intensity
- **Climate Stress Testing** — IPCC-aligned scenarios with resilience scoring
- **AI Copilot** — Natural language queries over live grid data

## Quick Start

### 1. Start Infrastructure

```bash
docker compose up -d
```

### 2. Start Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

### 3. Start Grid Simulator

```bash
cd simulator
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** for the command center.

API docs: **http://localhost:8100/docs**

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/site/overview` | GET | Live site metrics |
| `/api/v1/telemetry/multi` | GET | Multi-metric history |
| `/api/v1/forecast` | GET | 24h AI forecast |
| `/api/v1/optimize` | POST | Run battery dispatch optimization |
| `/api/v1/anomalies/detect` | POST | Scan for anomalies |
| `/api/v1/carbon/summary` | GET | Carbon audit report |
| `/api/v1/climate/stress-test` | GET | Climate scenario analysis |
| `/api/v1/copilot` | POST | AI natural language queries |
| `/api/v1/ws/live` | WS | Real-time telemetry stream |

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, scikit-learn, PuLP
- **Database**: PostgreSQL + TimescaleDB
- **Cache/PubSub**: Redis
- **MQTT**: Eclipse Mosquitto
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Recharts
- **External APIs**: Open-Meteo (weather), NYISO load/carbon models
