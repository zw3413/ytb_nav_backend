import os
from dotenv import load_dotenv

# Determine which environment file to load
ENV = os.getenv('ENV', 'development')  # default to development

print(ENV)

if ENV == 'production':
    load_dotenv('.env')
elif ENV == 'development':
    load_dotenv('.env.dev')
else:
    load_dotenv('.env.local')  # for local testing
