#!/bin/bash
# Database Migration Script for Market Matrix

set -e

echo "🔄 Starting database migration process..."

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('Database is ready')
        exit(0)
except Exception as e:
    print(f'Database not ready (attempt {attempt}/{max_attempts}): {e}')
    exit(1)
" 2>/dev/null; then
        echo "✅ Database is ready!"
        break
    fi

    echo "⏳ Waiting 2 seconds... (attempt $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Database failed to become ready after $max_attempts attempts"
    exit 1
fi

# Check if we need to initialize alembic
echo "🔍 Checking Alembic configuration..."
if [ ! -d "alembic/versions" ]; then
    echo "📁 Creating alembic directories..."
    mkdir -p alembic/versions
fi

# Run alembic migrations
echo "🚀 Running Alembic migrations..."
alembic upgrade head

echo "✅ Database migration completed successfully!"

# Create initial data if needed
echo "📝 Creating initial data..."
python -c "
import asyncio
from app.core.database import get_session
from app.models.database.user import User
from app.services.security import hash_password

async def create_initial_data():
    async with get_session() as session:
        # Create a test user if no users exist
        result = await session.execute('SELECT COUNT(*) FROM users')
        user_count = result.scalar()

        if user_count == 0:
            print('Creating initial admin user...')
            admin_user = User(
                email='admin@marketmatrix.local',
                password_hash=hash_password('admin123'),
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print('✅ Initial admin user created (admin@marketmatrix.local / admin123)')
        else:
            print('✅ Users already exist, skipping initial user creation')

asyncio.run(create_initial_data())
" 2>/dev/null || echo "ℹ️ Initial data creation skipped or failed"

echo "🎉 Database initialization complete!"