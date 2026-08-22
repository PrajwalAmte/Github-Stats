#!/bin/bash
# Development helper script

set -e

case "$1" in
  setup)
    echo "🚀 Setting up development environment..."
    python3 setup.py
    ;;
  
  run)
    echo "🏃 Starting development server..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ;;
  
  test)
    echo "🧪 Running tests..."
    pytest -v
    ;;
  
  lint)
    echo "🔍 Running linter..."
    ruff check app/ tests/
    ;;
  
  format)
    echo "✨ Formatting code..."
    ruff format app/ tests/
    ;;
  
  migrate)
    echo "🗄️  Running migrations..."
    alembic upgrade head
    ;;
  
  sync)
    if [ -z "$2" ]; then
      echo "Usage: ./dev.sh sync <username>"
      exit 1
    fi
    
    echo "🔄 Syncing user: $2"
    
    # Load .env
    if [ -f .env ]; then
      export $(grep -v '^#' .env | xargs)
    fi
    
    curl -X POST "http://localhost:8000/v1/sync/$2" \
      -H "Authorization: Bearer $SYNC_SECRET" \
      -H "Content-Type: application/json" \
      | python -m json.tool
    ;;
  
  *)
    echo "GitHub Stats Service - Development Helper"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup          Run initial setup"
    echo "  run            Start development server"
    echo "  test           Run test suite"
    echo "  lint           Run linter"
    echo "  format         Format code"
    echo "  migrate        Run database migrations"
    echo "  sync <user>    Trigger sync for a user"
    echo ""
    ;;
esac
