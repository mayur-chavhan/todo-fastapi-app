# Import the function to create a database engine (connection pool)
from sqlalchemy import create_engine

# Import sessionmaker to generate Session classes for ORM operations
from sqlalchemy.orm import sessionmaker

# Import declarative_base to define ORM models using the declarative system
from sqlalchemy.ext.declarative import declarative_base

# Name of our SQLite database file
db_name = "todos-app.db"

# # Build the database URL pointing to the local SQLite file
SQLALCHEMY_DATABASE_URL = (
    f"sqlite:///./{db_name}"  # resolves to sqlite:///./todos-app.db
)

# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Westlife@localhost/TodoAppDB"

# Create the SQLAlchemy engine which manages connections to the database
# Below connection is only for SQlite 3 database connection
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },  # needed for SQLite to allow usage in multiple threads
)
# Below engine is connecting to the Postgresql database
# engine = create_engine(SQLALCHEMY_DATABASE_URL)
# Create a configured Session class
SessionLocal = sessionmaker(
    autocommit=False,  # disable auto-commit; you must call .commit() explicitly
    autoflush=False,  # disable auto-flush; flush occurs only on commit or explicit .flush()
    bind=engine,  # bind this session to our engine
)

# Base class for all ORM models; subclasses will define database tables
Base = declarative_base()
