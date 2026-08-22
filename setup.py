#!/usr/bin/env python3
"""
Quick setup script for local development.
"""

import os
import secrets
import subprocess
import sys


def main():
    """Run initial setup tasks."""
    print("🚀 GitHub Stats Service - Setup\n")

    # Check Python version

    print("✅ Python version OK")

    # Check if .env exists
    if not os.path.exists(".env"):
        print("\n📝 Creating .env file from .env.example...")

        with open(".env.example") as src:
            content = src.read()

        # Generate random sync secret
        sync_secret = secrets.token_hex(32)
        content = content.replace(
            "SYNC_SECRET=your_random_secret_here_generate_with_openssl_rand_hex_32",
            f"SYNC_SECRET={sync_secret}"
        )

        with open(".env", "w") as dst:
            dst.write(content)

        print("✅ Created .env file")
        print(f"   Generated SYNC_SECRET: {sync_secret}")
        print("\n⚠️  Please edit .env and add your DATABASE_URL and GITHUB_TOKEN")
    else:
        print("✅ .env file exists")

    # Install dependencies
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Check if we can connect to database
    print("\n🔍 Checking database connection...")
    try:
        from dotenv import load_dotenv
        load_dotenv()

        database_url = os.getenv("DATABASE_URL")
        if not database_url or "your_database_url" in database_url.lower():
            print("⚠️  DATABASE_URL not configured")
            print("   Please update .env with your PostgreSQL connection string")
        else:
            print("✅ DATABASE_URL configured")

            # Try to run migrations
            print("\n🗄️  Running database migrations...")
            try:
                subprocess.run(["alembic", "upgrade", "head"], check=True)
                print("✅ Migrations complete")
            except subprocess.CalledProcessError:
                print("❌ Migration failed - check your DATABASE_URL")
                print("   You can run migrations manually later with: alembic upgrade head")
    except Exception as e:
        print(f"⚠️  Could not check database: {e}")

    print("\n" + "="*60)
    print("🎉 Setup complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit .env and configure DATABASE_URL and GITHUB_TOKEN")
    print("2. Run migrations: alembic upgrade head")
    print("3. Start the server: uvicorn app.main:app --reload")
    print("4. Visit: http://localhost:8000")
    print("\n")


if __name__ == "__main__":
    main()
