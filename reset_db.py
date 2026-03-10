from database import engine, Base
import models

print("🚨 Dropping all old tables...")
Base.metadata.drop_all(bind=engine)

print("🏗️ Rebuilding tables with new strict constraints...")
Base.metadata.create_all(bind=engine)

print("✅ Database successfully reset!")