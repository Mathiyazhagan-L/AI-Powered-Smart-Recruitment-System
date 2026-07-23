from sqlalchemy.orm import declarative_base

# Central declarative base used by all models in the project.
# Import `Base` from `core.base` in model files to avoid multiple
# Base instances which prevent tables from being created together.
Base = declarative_base()
