from app import db, app
from models import Job
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_cancelled_column():
    """Add cancelled column to the jobs table if it doesn't exist"""
    with app.app_context():
        # Use pure raw SQL for the check and add column operation
        conn = db.engine.connect()
        transaction = conn.begin()

        try:
            # Check if column exists using information_schema
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name='jobs' AND column_name='cancelled')"
            ))
            column_exists = result.scalar()
            
            if column_exists:
                logger.info("The 'cancelled' column already exists in the jobs table.")
            else:
                logger.info("The 'cancelled' column does not exist. Adding it now...")
                
                # Execute raw SQL to add the column
                conn.execute(text('ALTER TABLE jobs ADD COLUMN cancelled BOOLEAN DEFAULT FALSE NOT NULL'))
                logger.info("Successfully added 'cancelled' column to the jobs table.")
                
            # Commit the transaction
            transaction.commit()
            
        except Exception as e:
            # Rollback the transaction if an error occurs
            transaction.rollback()
            logger.error(f"Error adding 'cancelled' column: {str(e)}")
            raise
        finally:
            # Close the connection
            conn.close()

if __name__ == "__main__":
    add_cancelled_column()
