# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-06-25

### Added
- **Fraud Detection Engine**: Multi-signal behavioral scoring (IP velocity, User velocity, Text duplication, ML confidence).
- **Dual Authentication**: Implemented Google OAuth 2.0 (via Authlib) for citizens alongside standard local auth.
- **Admin Review Workflow**: Admins can now mark flagged complaints as 'Genuine' or 'Fake' directly from the dashboard.
- **Enhanced Tracking**: Upgraded SQLite schema to link complaints directly to authenticated users while retaining guest support.
- **Security Hardening**: Replaced `hash()` with cryptographic `SHA-256` for document integrity verification.

### Changed
- **Architecture**: Refactored monolithic routing into Flask Blueprints (auth, user_auth, complaints, dashboard, reports, status).
- **Service Layer**: Extracted classification, email, and PDF generation into decoupled service modules (`services/`).
- **Database Migrations**: Introduced lightweight `try/except` auto-migrations in `models/db.py`.

## [1.0.0] - 2026-06-21

### Added
- **AI Classification Engine**: Added Scikit-learn pipeline (TF-IDF + Multinomial NB) for 13 distinct grievance categories.
- **Automated Summarization**: Integrated regex-based entity extraction and summarization logic.
- **Citizen Portal**: Responsive public UI for submitting complaints with real-time feedback.
- **Tracking System**: Interactive timeline for citizens to track complaint status via unique ID.
- **Admin Dashboard**: Secured portal with Chart.js analytics and recent complaint management.
- **PDF Report Generation**: Integrated ReportLab for professional, branded PDF documents.
- **Security Baseline**: Added rate limiting (Flask-Limiter), secure HTTP headers, and strict request logging.
- **Cloud Readiness**: Added Procfile, `render.yaml`, `runtime.txt`, and Gunicorn support for Render/Railway deployment.
