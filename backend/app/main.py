
from fastapi import FastAPI

app = FastAPI(
    title="PrivacyLens API",
    description="Intelligent PII Detection and Text Anonymization",
    version="0.1.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to PrivacyLens API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
