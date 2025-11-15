#!/usr/bin/env python3
"""
Fix admin password in database
"""
import asyncio
from sqlalchemy import text
import sys
import os

# Add app to path
sys.path.insert(0, '/app')

from app.core.security import get_password_hash, verify_password
from app.core import database


async def main():
    print("Connecting to database...")
    await database.init_databases()

    # Generate new hash
    new_hash = get_password_hash('admin')
    print(f"Generated hash for password 'admin': {new_hash[:50]}...")

    # Get current hash from database
    async with database.postgres_engine.begin() as conn:
        result = await conn.execute(
            text("SELECT email, hashed_password FROM users WHERE email = 'admin'")
        )
        row = result.first()

        if row:
            current_hash = row[1]
            print(f"\nCurrent hash in DB: {current_hash[:50]}...")

            # Test current hash
            is_valid = verify_password('admin', current_hash)
            print(f"Current hash validates: {is_valid}")

            # Test new hash
            is_new_valid = verify_password('admin', new_hash)
            print(f"New hash validates: {is_new_valid}")

            if not is_valid:
                print("\n❌ Current password is incorrect. Updating...")
                await conn.execute(
                    text("UPDATE users SET hashed_password = :hash WHERE email = 'admin'"),
                    {"hash": new_hash}
                )
                print("✅ Password updated successfully!")
            else:
                print("\n✅ Password is already correct!")
        else:
            print("❌ Admin user not found!")

    await database.close_databases()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
