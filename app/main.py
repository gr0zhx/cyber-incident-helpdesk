from fastapi import FastAPI

app = FastAPI(
    title="Helpdesk Keamanan Siber Pusdatin",
    description="Sistem helpdesk multi-agent untuk pra-triase insiden keamanan siber",
    version="0.1.0",
)


@app.get("/")
def root() -> dict:
    return {"status": "ok"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "helpdesk-api"}
