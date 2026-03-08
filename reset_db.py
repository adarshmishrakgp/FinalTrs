from database import engine
import models

print("Starting database reset...")

# Drop the old tables
models.Base.metadata.drop_all(bind=engine)
print("Old tables dropped.")

# Recreate the tables with the new Master Sheet columns
models.Base.metadata.create_all(bind=engine)
print("New tables created successfully!")