# Project Overview for Recruiters

**Voice2Justice** is a comprehensive software engineering portfolio piece that demonstrates end-to-end full-stack development, machine learning integration, and security-first system design.

## What it does (Plain English)
When citizens face issues—whether it's a stolen bicycle or a broken water pipe—they often don't know which department to contact or which legal terms to use. Voice2Justice allows citizens to simply type what happened in their own words. The platform's Artificial Intelligence reads the text, figures out exactly what type of issue it is, tags it with the correct legal or municipal code, and automatically generates a professional, verifiable PDF report for the correct government department.

## Why this project stands out

Most student projects are simple CRUD (Create, Read, Update, Delete) applications. Voice2Justice elevates itself by solving real-world engineering and architectural challenges:

1. **Practical Machine Learning Integration**: Rather than just analyzing a dataset in a Jupyter Notebook, this project embeds a trained Scikit-learn model directly into a web application's request lifecycle, processing real-time user input.
2. **Production-Minded Security**: It goes beyond basic passwords. It implements XSS protection, rate limiting, secure HTTP headers, cryptographic hashing (SHA-256) for document integrity, and IDOR prevention using UUIDv4 tracking IDs.
3. **Graceful Degradation**: If the ML model file is missing or fails to load, the system doesn't crash; it seamlessly falls back to a custom keyword-scoring algorithm.
4. **Asynchronous Processing**: It recognizes the limitations of single-worker web servers by decoupling slow operations (like sending SMTP emails) into background threads.
5. **Nuanced Fraud Detection**: Instead of blocking users (which is dangerous in an emergency reporting app), it uses a multi-factor behavioral algorithm to calculate a "Fraud Score" and flag suspicious activity for human review.

## Technical Skills Demonstrated

- **Backend Engineering**: Python, Flask, Blueprint Architecture, RESTful API design.
- **Machine Learning**: Natural Language Processing (NLP), Scikit-learn, TF-IDF Vectorization, Naive Bayes Classification.
- **Database Design**: SQLite, schema design, raw parameterized SQL queries, zero-downtime auto-migrations.
- **Security & Authentication**: Google OAuth 2.0 (OIDC), Session management, Password Hashing, Rate Limiting.
- **Frontend Integration**: Jinja2 templating, Bootstrap 5 responsive design, Chart.js data visualization.
- **DevOps & Deployment**: Gunicorn, Environment variable management, PaaS deployment configuration (Render).
