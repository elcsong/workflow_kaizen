# Installation Guide

This guide covers setting up the project on a Windows machine. It's designed for easy portability between personal and company PCs. Always use a virtual environment to avoid conflicts with system-wide packages.

## Prerequisites
- Python 3.8 or higher (Download from [python.org](https://www.python.org/))
- Git (Download from [git-scm.com](https://git-scm.com/))
- Optional: Cursor AI for development (integrated with VS Code)

## Step-by-Step Installation

1. **Clone the Repository**
   ```
   git clone https://github.com/LazyButSmart/workflow-kaizen.git
   cd workflow-kaizen
   ```

2. **Create a Virtual Environment** (Highly recommended for isolation and portability)
   - Using venv:
     ```
     python -m venv kaizen-venv
     # On Windows:
     kaizen-venv\Scripts\activate
     # On macOS/Linux:
     source kaizen-venv/bin/activate
     ```
   - Using conda (if installed):
     ```
     conda create -n workflow-kaizen python=3.8
     conda activate workflow-kaizen
     ```
   Note: On company PC, this prevents conflicts with existing software. Deactivate with `deactivate` or `conda deactivate`.

3. **Install Dependencies**
   ```
   pip install -r requirements.txt
   ```
   If requirements.txt doesn't exist yet, create it with `pip freeze > requirements.txt` after installing packages.

4. **Configure Environment Variables**
   - Copy `.env.example` to `.env`:
     ```
     copy .env.example .env
     ```
   - Edit `.env` with your values (e.g., DB_URL, API_KEY). Do NOT commit .env to Git.

5. **Test the Setup**
   - Run a simple test script if available, or:
     ```
     python -c "import pandas; print('Setup successful!')"
     ```
   - If issues arise on company PC (e.g., firewall, permissions), check Windows Defender settings or run as admin.

## Troubleshooting
- **Permission Errors**: Run Command Prompt as Administrator.
- **Package Conflicts**: Ensure virtual environment is activated.
- **Portability Issues**: Test on a similar Windows setup; avoid hard-coded paths—use relative paths.
- For more help, check [usage.md](usage.md) or contact me.

