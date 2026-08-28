from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.routes.bills import router as bills_router

app = FastAPI(title="Bill Processor POC")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Guarantee Access-Control-Allow-Origin header on ALL responses (including uncaught 500 errors)
@app.middleware("http")
async def ensure_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=200)
    else:
        try:
            response = await call_next(request)
        except Exception as exc:
            response = JSONResponse(
                status_code=500,
                content={"detail": f"Internal Server Error: {str(exc)}"}
            )

    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"

    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bills_router, prefix="/api/bills", tags=["bills"])

@app.get("/")
def root():
    # Reload trigger
    return {"status": "ok"}

