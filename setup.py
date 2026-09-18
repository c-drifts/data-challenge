#!/usr/bin/env python3
"""
Setup script for Data Challenge pipeline.
Initializes environment, installs dependencies, and prepares the database.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VENV_DIR = PROJECT_ROOT / ".venv"


def get_venv_python():
    """Return the Python executable inside the virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def get_activate_command():
    """Return the shell command to activate the virtual environment."""
    if sys.platform == "win32":
        return r".venv\Scripts\activate"
    return "source .venv/bin/activate"


def create_venv():
    """Create a virtual environment if it does not exist."""
    print("\nCreating virtual environment...")
    if VENV_DIR.exists():
        print(f"OK: Virtual environment already exists at {VENV_DIR}")
        return

    try:
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        print(f"OK: Virtual environment created at {VENV_DIR}")
    except subprocess.CalledProcessError:
        print("ERROR: Failed to create virtual environment")
        sys.exit(1)


def check_python_version():
    """Verify Python 3.10+"""
    if sys.version_info < (3, 10):
        print(f"ERROR: Python 3.10+ required. Current: {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"OK: Python {sys.version_info.major}.{sys.version_info.minor}")


def install_requirements():
    """Install Python dependencies into the virtual environment"""
    print("\nInstalling Python dependencies...")
    requirements_file = PROJECT_ROOT / "requirements.txt"
    if not requirements_file.exists():
        print(f"ERROR: {requirements_file} not found")
        sys.exit(1)

    python_executable = get_venv_python()
    if not python_executable.exists():
        print(f"ERROR: Virtual environment Python not found at {python_executable}")
        sys.exit(1)

    try:
        subprocess.run(
            [str(python_executable), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
            check=True,
        )
        subprocess.run(
            [str(python_executable), "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
        )
        print("OK: Dependencies installed in virtual environment")
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies")
        sys.exit(1)


def check_docker():
    """Check if Docker is available"""
    print("\nChecking Docker...")
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        print("OK: Docker is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("WARNING: Docker not found. You can still run the pipeline using local CSV files in data/")
        return False


def create_database():
    """Create SQLite database and schema"""
    print("\nInitializing SQLite database...")
    db_path = Path(__file__).parent / "data.db"
    schema_path = Path(__file__).parent / "src" / "schema.sql"

    if not schema_path.exists():
        print(f"ERROR: {schema_path} not found")
        sys.exit(1)

    import sqlite3

    try:
        conn = sqlite3.connect(str(db_path))
        with open(schema_path, "r") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print(f"OK: Database created at {db_path}")
    except Exception as e:
        print(f"ERROR: Failed to create database: {e}")
        sys.exit(1)


def main():
    """Run setup steps"""
    print("="*60)
    print("Data Challenge - Setup")
    print("="*60)

    check_python_version()
    create_venv()
    install_requirements()
    docker_available = check_docker()
    create_database()

    activate_cmd = get_activate_command()

    print("\n" + "="*60)
    print("Setup completed successfully!")
    print("="*60)

    print("\nNext steps:")
    print(f"1. Activate the virtual environment: {activate_cmd}")
    if docker_available:
        print("2. Start Docker API: docker compose up -d")
        print("3. Run pipeline: python src/main.py")
    else:
        print("2. Run pipeline with local data: python src/main.py")
        print("   (Uses CSV files from data/ directory)")

    print("\nQuery results: sqlite3 data.db")


if __name__ == "__main__":
    main()
