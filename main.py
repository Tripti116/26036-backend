from fastapi import FastAPI
from routes import auth, instruments, verification, certificates

app = FastAPI()

# ✅ Root route to confirm server is alive
@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

# Include your routers
app.include_router(auth.router)
app.include_router(instruments.router)
app.include_router(verification.router)
app.include_router(certificates.router)
