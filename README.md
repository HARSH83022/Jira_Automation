# DC-AI Sprint Development Report Automation

A local-first sprint reporting application that takes a Jira CSV export, calculates deterministic sprint and developer story-point metrics, generates a professional Excel report, and stores report history in SQLite.

## What this project does

- Upload one or two Jira CSV exports (morning and EOD)
- Validate CSV structure before processing
- Detect available Jira columns and handle missing optional fields without crashing
- Calculate developer assigned/completed/remaining SP and completion percentages
- Produce an Excel workbook in the required DC-AI report format
- Store generated reports in SQLite and allow download/history browsing
- Provide a simple React + TypeScript dashboard for sprint summary and report history
- Keep all core calculations deterministic and AI-free

## Architecture

- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + SQLite
- Excel generation: openpyxl
- Data parsing: pandas
- Report workflow: CSV validation → calculation engine → Excel generation → DB persistence

## Project structure

- backend/app/
  - api/
  - calculations/
  - datasources/
  - integrations/
  - models/
  - schemas/
  - services/
- frontend/src/
- generated_reports/
- uploads/
- .env.example
- .gitignore

## Requirements

- Python 3.11+
- Node.js 18+
- npm

## Backend setup

1. Open a terminal in the project root.
2. Create and activate a virtual environment:

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

3. Install backend dependencies:

   cd backend
   python -m pip install -r requirements.txt

4. Start the API:

   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

## Frontend setup

1. In a second terminal:

   cd frontend
   npm install
   npm run dev -- --host 0.0.0.0 --port 3000

2. Open the app in the browser at http://localhost:3000. The Vite development proxy forwards `/api` requests to the backend on port 8001.

## Environment variables

A sample environment file is provided at .env.example. Copy it to a real .env file if you need custom configuration.

Example values:

- APP_ENV=development
- DATABASE_URL=sqlite:///./dc_ai_reports.db
- REPORT_STORAGE_PATH=./generated_reports
- MAX_UPLOAD_SIZE_MB=20

Outlook and AI values remain optional for the current local core workflow.

## Using the application

1. Open the frontend dashboard.
2. Go to Upload CSV.
3. Select the EOD Jira CSV export.
4. Optionally add a Morning CSV.
5. Submit the form to generate the sprint report.
6. Review the generated summary and warnings.
7. Download the generated Excel report from the report screen or history page.

## CSV validation rules

The parser validates that the file contains:

- Issue key or Summary
- Status

It also handles optional fields gracefully and records warnings such as:

- Missing story points
- Missing developer allocation
- Missing status
- Unknown developer
- Duplicate allocation

## Excel output

The generated workbook includes:

- Sprint title and snapshot metadata
- Overall sprint progress section
- Developer progress table
- Story summary totals
- Professional formatting and page layout for printing

## Testing

Run backend tests:

cd backend
python -m pytest -q

Run frontend build verification:

cd frontend
npm run build

## Current verification status

This project was verified with the supplied Jira sample file.

Observed result on the sample export:

- 118 stories detected
- 21 stories missing story points
- 1 story missing developer allocation
- Total scope: 277.60 SP
- Completion: 38.72%

## Notes

- The core reporting engine is deterministic and does not use AI to calculate numbers.
- AI and Outlook integration are prepared as optional layers, but the local reporting flow works without them.
- The current implementation is designed to be extended to Jira REST API and Outlook OAuth later without changing the core calculation logic.

## Production deployment

### Render (GitHub deployment)

This repository includes a `Dockerfile` and `render.yaml` for a single-service
Render deployment. The container builds the React frontend and serves it from
the FastAPI application, so the deployed app uses one URL and does not need a
separate frontend proxy.

1. In Render, choose **New → Blueprint**.
2. Connect the GitHub repository `HARSH83022/Jira_Automation`.
3. Select the `main` branch and apply `render.yaml`.
4. Deploy the service and open the generated `onrender.com` URL.
5. Add `GEMINI_API_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, and any Outlook
   credentials in Render environment variables only; never commit them.

The deterministic report workflow does not require Gemini. Set
`DEFAULT_AI_PROVIDER=gemini` only after adding a valid `GEMINI_API_KEY`.
The default deployment intentionally uses `none` so offline AI availability
cannot block report generation.

The default Render filesystem is ephemeral. Use a Render persistent disk or
external PostgreSQL/object storage if report history and generated Excel files
must survive service restarts.
