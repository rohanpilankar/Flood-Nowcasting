# FloodWatch AI: Urban Flood Nowcasting & Safe Mobility System

**SIH26085 — AI-Powered Urban Flood Nowcasting & Safe Mobility System (Greater Mumbai / BMC Area)**

> **FloodWatch AI** is an AI-powered urban flood nowcasting and safe mobility platform for Greater Mumbai. It combines high-resolution GIS topological layers, Machine Learning (XGBoost), FastAPI microservices, an Angular standalone frontend, Role-Based Access Control (RBAC), consent-gated citizen safety warnings, and flood-aware routing to predict water inundation depths and guide citizens along safe transit corridors.

---

## Key Features

- **Hyper-Local Flood Risk Nowcasting**: Predicts water accumulation and flood risk across 500m spatial grids in Greater Mumbai (covering Dadar, Hindmata, Kurla, Andheri Subway, Bandra BKC, Gandhi Market, Sion, etc.) across 5 forecast horizons (`Now`, `+15m`, `+30m`, `+45m`, `+60m`).
- **Safe Route Planning**: A flood-aware pathfinding engine that penalizes submerged road links and calculates safer detour routes with water depth profiles.
- **Three-Tier Role-Based Access Control (RBAC)**:
  - **Citizen**: Personalized dashboard, real-time hazard warnings, flood observation reporting, and self-service privacy controls.
  - **Government Authority (EOC Officer)**: Municipal operations console displaying aggregate citizen counts within flood polygons (*"125 Opted-In, 112 Notified"*) and emergency warning broadcast dispatching.
  - **System Administrator**: User management, municipal authority verification, citizen feedback review, and AI model concordance evaluation.
- **Consent-Gated Location Architecture**: Strict opt-in location sharing. No automatic page-load tracking; exact citizen coordinates are never publicly exposed; self-service instant session purge and history erasure.
- **Ground-Truth Validation**: Citizens submit crowd-sourced flood observations (water depth, traffic status, rainfall intensity) to ground-truth and continuously evaluate ML model predictions.

---

## Tech Stack

- **Frontend**: Angular 19/21 (Standalone Components, Signals, Reactive Forms, SCSS)
- **Mapping & GIS**: Leaflet, GeoJSON, Shapely
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy, Uvicorn
- **Machine Learning**: XGBoost, Scikit-Learn, Joblib (18 hydrodynamic topological features)
- **Database**: Dual-mode support (SQLite + Shapely for zero-setup local development; PostgreSQL + PostGIS ready for production)
- **Security**: JWT (python-jose), bcrypt password hashing

---

## Project Structure

```text
Flood-Nowcasting/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/routes/       # REST API endpoints (auth, alerts, locations, feedback, gov, admin)
│   │   ├── core/             # Security, JWT, configuration
│   │   ├── db/               # SQLAlchemy models and database session
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic (nowcasting, routing, auth, alerts, feedback)
│   │   └── main.py           # FastAPI entrypoint
├── data/                     # GIS and geospatial datasets
│   ├── raw/                  # Mumbai boundary, drainage network, flood hotspots, AWS rainfall
│   ├── processed/            # 500m spatial grids and feature matrices
│   └── final/                # Engineered ML training datasets
├── docs/                     # Technical documentation & model cards
│   ├── API.md
│   ├── MODEL_CARD.md
│   ├── DATA_PIPELINE.md
│   └── FEATURE_DICTIONARY.md
├── models/                   # Trained ML models and scalers
│   ├── metadata/             # Scalers and metrics comparison
│   └── trained/              # Trained XGBoost models
├── src/                      # Angular Frontend Application
│   ├── app/
│   │   ├── core/             # Auth, guards, interceptors, providers, services
│   │   ├── features/         # Citizen dashboard, Gov EOC, Admin, Flood map, Safe route, Auth
│   │   └── shared/           # Reusable UI components (gauges, badges, stat cards, modals)
│   └── styles/               # Glassmorphic design system and CSS tokens
└── tests/                    # Automated pytest test suite
    ├── test_api.py           # Phase 2 nowcasting and routing tests
    └── test_extension.py     # Auth, RBAC, targeted alerts, and ground-truth tests
```

---

## Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/rohanpilankar/Flood-Nowcasting.git
cd Flood-Nowcasting

# Install Python dependencies
pip install fastapi uvicorn sqlalchemy bcrypt python-jose pydantic shapely geopandas xgboost scikit-learn joblib pytest httpx

# Start the FastAPI server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
FastAPI interactive Swagger documentation will be available at: `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
```bash
# In the project root
npm install

# Start the Angular development server
npm start
# or: npx ng serve
```
Open your browser at `http://localhost:4200/`.

---

## Demo Accounts

The database is auto-seeded with test accounts for all user roles:

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@floodwatch.mumbai.gov.in` | `Admin@Mumbai2026` | Full system command, RBAC, model evaluation |
| **EOC Officer** | `eoc.officer@mcgm.gov.in` | `Gov@Mumbai2026` | Verified government authority, emergency broadcast |
| **Citizen** | `rohan.citizen@gmail.com` | `Citizen@2026` | Citizen safety portal, personal alerts, ground-truth reporting |

*(Note: The login page includes quick 1-click switcher buttons to populate these credentials instantly).*

---

## Running Automated Tests

Run the full pytest suite covering nowcasting, routing, RBAC, targeted alerts, and ground truth validation:
```bash
python -m pytest tests/test_api.py tests/test_extension.py -v
```

---

## License

This project is developed for **Smart India Hackathon (SIH26085)** under the Municipal Corporation of Greater Mumbai (BMC) Disaster Management Cell guidelines.
