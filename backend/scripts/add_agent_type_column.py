#!/usr/bin/env python3
"""
Migration script to add agent_type and agent_state columns to sessions table
"""
import sqlite3
import os
from pathlib import Path

def migrate():
    # Use the database path directly
    db_path = Path(__file__).parent.parent / 'health_assistant.db'
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"Current columns in sessions table: {columns}")
        
        # Add agent_type column if it doesn't exist
        if 'agent_type' not in columns:
            print("Adding agent_type column...")
            cursor.execute("""
                ALTER TABLE sessions 
                ADD COLUMN agent_type VARCHAR(50) DEFAULT 'general' NOT NULL
            """)
            print("✓ agent_type column added")
        else:
            print("✓ agent_type column already exists")
        
        # Add agent_state column if it doesn't exist
        if 'agent_state' not in columns:
            print("Adding agent_state column...")
            cursor.execute("""
                ALTER TABLE sessions 
                ADD COLUMN agent_state JSON
            """)
            print("✓ agent_state column added")
        else:
            print("✓ agent_state column already exists")
        
        # Create index on agent_type if it doesn't exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name='ix_sessions_agent_type'
        """)
        if not cursor.fetchone():
            print("Creating index on agent_type...")
            cursor.execute("""
                CREATE INDEX ix_sessions_agent_type ON sessions(agent_type)
            """)
            print("✓ Index created")
        else:
            print("✓ Index already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(sessions)")
        print("\nUpdated table structure:")
        for row in cursor.fetchall():
            print(f"  {row[1]}: {row[2]}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
