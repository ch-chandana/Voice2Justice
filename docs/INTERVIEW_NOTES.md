# Interview Preparation & Resume Notes

This document contains optimized descriptions and talking points for recruiters and technical interviews, based strictly on the implemented features of Voice2Justice.

## Resume Bullet Points

### ATS-Friendly Project Titles
- Voice2Justice: AI-Powered Grievance Routing Platform
- Full-Stack Legal Intelligence System
- Automated Complaint Classification Engine

### 2-Line Resume Description
- Architected a full-stack Flask platform that utilizes a Scikit-learn Machine Learning pipeline (TF-IDF + Naive Bayes) to automatically classify and route unstructured citizen complaints into 13 legal categories.
- Implemented a multi-signal fraud detection engine, dual authentication (Google OAuth), and automated ReportLab PDF generation, secured by rate limiting and cryptographic document hashing.

### 4-Line Resume Description
- **Voice2Justice (Flask, Python, Scikit-learn, SQLite)**
- Built an intelligent governance routing platform that leverages NLP and a Multinomial Naive Bayes classifier to parse unstructured citizen complaints and map them to relevant legal codes.
- Engineered a robust backend featuring daemon-threaded asynchronous email delivery, automatic SQLite migrations, and cryptographic SHA-256 PDF report integrity verification.
- Designed a defense-in-depth security architecture including IP/user velocity fraud scoring, Flask-Limiter rate throttling, and Google OAuth 2.0 integration via Authlib.
- Developed an admin analytics dashboard utilizing Chart.js to visualize grievance volume trends and category distribution in real-time.

---

## Online Portfolios & LinkedIn

### LinkedIn Description
**Voice2Justice | AI-Powered Citizen Grievance Routing Platform**
I built a full-stack intelligence platform designed to bridge the gap between civilians and government authorities. Using a custom Scikit-learn Machine Learning pipeline (TF-IDF + Multinomial Naive Bayes), the system instantly classifies unstructured complaints into 13 legal/civic categories and extracts street-level entity data. 

To ensure production-readiness, I implemented a robust fraud detection engine tracking IP and user velocity, secured the application with Google OAuth and strict HTTP headers, and decoupled heavy operations like SMTP email delivery into asynchronous daemon threads. The platform automatically generates branded, verifiable PDF reports (First Information Reports) complete with QR tracking and SHA-256 cryptographic hashing. 
*Tech Stack: Python, Flask, Scikit-learn, SQLite, OAuth 2.0, ReportLab, Bootstrap 5.*

---

## Verbal Pitching (Interviews)

### 30-Second Elevator Pitch
"I built Voice2Justice, an AI-powered platform that automatically categorizes unstructured citizen complaints and routes them to the correct government department. It uses a Scikit-learn machine learning pipeline to map natural language to specific legal and municipal codes. It features a full admin analytics dashboard, multi-signal fraud detection, and auto-generates cryptographically hashed PDF reports. It's built with Flask and Python, and demonstrates my ability to integrate machine learning into a secure, full-stack web application."

### 2-Minute Technical Explanation
"For my flagship project, Voice2Justice, I wanted to solve the bureaucratic bottleneck of manually sorting citizen complaints. I built the backend in Flask, using a modular blueprint architecture to separate concerns like authentication, routing, and reporting. 

The core feature is the ML engine. I curated a dataset of complaints and trained a Scikit-learn pipeline using a TF-IDF vectorizer and a Multinomial Naive Bayes classifier. When a user submits a complaint, the system extracts location entities using Regex, runs the text through the model, and classifies it into one of 13 specific crime or civic categories—even attaching the relevant legal codes, like BNS sections.

To make it production-ready, I had to solve a few engineering challenges. First, I couldn't have the server hang while sending emails, so I decoupled SMTP delivery into background daemon threads. Second, to prevent spam without blocking urgent legitimate complaints, I built a multi-signal fraud scoring system that calculates a risk score based on IP velocity and ML confidence, flagging it for admin review rather than hard-rejecting it. Finally, I used ReportLab to generate official PDF reports on the fly, embedding a SHA-256 hash of the complaint data so authorities can verify the document hasn't been tampered with. It's fully deployed on Render with Gunicorn."

---

## Anticipated Interview Questions & Answers

**Q: Why did you choose SQLite instead of PostgreSQL or MySQL?**
> "For the MVP and initial deployment, SQLite allowed for rapid iteration and zero-configuration deployment. I implemented an auto-migration script using `ALTER TABLE` in `try/except` blocks to handle schema evolution. However, in a real-world high-traffic scenario, SQLite's file-level locking would become a bottleneck for concurrent writes. The codebase uses standard SQL and parameterized queries, so migrating to PostgreSQL using `psycopg2` or an ORM like SQLAlchemy would be the immediate next step for horizontal scaling."

**Q: How did you handle long-running tasks like sending emails?**
> "I deployed this on a free-tier PaaS which uses a single web worker. If I sent the email synchronously in the HTTP request cycle, the server would block for 10+ seconds, potentially causing Gunicorn timeouts. To solve this without the overhead of setting up Celery and Redis, I spawned standard Python `threading.Thread` daemon threads for the SMTP calls. It's a lightweight fire-and-forget solution appropriate for this scale."

**Q: How does your fraud detection work?**
> "Instead of blocking users with CAPTCHAs—which is bad UX for someone reporting an urgent crime—I built a behavioral scoring engine. It calculates a score from 0 to 1.0 based on signals like IP submission velocity, user ID velocity, exact string duplication, and the confidence score from the ML model. If the score exceeds 0.4, it flags it as 'Review Required', and above 0.7 as 'Suspicious'. The complaint is still saved and routed, but the admin dashboard highlights it for human review."
