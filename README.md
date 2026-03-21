# **AScribe – Personal Knowledge Intelligence System**

## Overview

AScribe is a lightweight, AI-powered knowledge management web application designed for students who want to transform their study materials into an intelligent, queryable knowledge base.

Users can upload a wide range of files—including PDFs, images, and handwritten notes—into personalized Vaults, where content is automatically processed, indexed, and made accessible through retrieval-augmented generation (RAG).

The platform enables users to search, summarize, and generate learning materials such as flashcards and quizzes, all grounded strictly in their own uploaded content—turning passive notes into an active learning system.

---

# Project Onboarding (Quick Setup)

## 1. Clone the Repository

```bash
git clone <repo-url>
cd <project-root>
```

## 2. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## 3. Setup Python Environment (Backend)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

## 4. Install Pre-Commit

Recommended (global):

```bash
pipx install pre-commit
```

Alternative:

```bash
pip install pre-commit
```

## 5. Enable Git Hooks

```bash
pre-commit install
```

## 6. Run Initial Lint/Format (Important)

```bash
pre-commit run --all-files
```

---

## Daily Workflow

```bash
git add .
git commit -m "message"
```

Pre-commit will automatically:

* Lint backend (Ruff)
* Lint frontend (ESLint)
* Format code (Prettier)

---

## Notes

* Make sure `frontend/node_modules` exists (run `npm install` if errors occur)
* Do not skip hooks unless necessary (`--no-verify`)

---
