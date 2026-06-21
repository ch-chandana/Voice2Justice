# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-21

### Added
- **AI Classification Engine**: Added Scikit-learn pipeline for 13 distinct grievance categories.
- **Automated Summarization**: Integrated spaCy-based NLP to extract entities and generate summaries.
- **Citizen Portal**: Responsive public UI for submitting complaints with real-time feedback.
- **Tracking System**: Interactive timeline for citizens to track complaint status via unique ID.
- **Admin Dashboard**: Secured portal with Chart.js analytics and recent complaint management.
- **PDF Report Generation**: Integrated ReportLab for professional, branded PDF documents featuring tracking QR codes and SHA-256 integrity hashes.
- **Security Hardening**: Added rate limiting (Flask-Limiter), secure HTTP headers, and strict request logging.
- **Cloud Readiness**: Added Procfile, `render.yaml`, `runtime.txt`, and Gunicorn support for Render/Railway deployment.
