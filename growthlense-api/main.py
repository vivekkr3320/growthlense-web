import os
from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from services.parser import parse_shopify_export
from services.metrics import calculate_metrics
from services.ai import generate_ai_insights

app = FastAPI(
    title="GrowthLense API",
    description="Sleek e-commerce math & AI analytics engine for Shopify exports",
    version="1.0.0"
)

# Configure CORS so our Next.js frontend can communicate smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "GrowthLense API is fully functional. Post your Shopify export to /analyze.",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    x_openai_key: Optional[str] = Header(None)
):
    # 1. Read file bytes
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    # 2. Parse Shopify order details
    df, parse_error = parse_shopify_export(content, file.filename)
    if parse_error:
        raise HTTPException(status_code=400, detail=parse_error)

    # 3. Calculate core KPIs & trends
    try:
        metrics = calculate_metrics(df)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error calculating core metrics: {str(e)}")

    # 4. Generate AI insights
    # Check if a custom key was passed in headers, otherwise look in env variables
    openai_key = x_openai_key if x_openai_key else os.environ.get("OPENAI_API_KEY", "")
    
    try:
        # We can dynamically pass the key
        from services.ai import generate_local_analyst_insights
        
        # Adjust generated insights dynamically if key is provided
        if openai_key and openai_key.strip() not in ["", "YOUR_API_KEY", "default"]:
            # Temporarily set environmental key or pass it
            # To avoid thread-safety concerns, we pass it or set env.
            # Let's set it in environment for this call, then restore
            old_key = os.environ.get("OPENAI_API_KEY")
            try:
                os.environ["OPENAI_API_KEY"] = openai_key
                insights = generate_ai_insights(metrics)
            finally:
                if old_key is not None:
                    os.environ["OPENAI_API_KEY"] = old_key
                else:
                    os.environ.pop("OPENAI_API_KEY", None)
        else:
            insights = generate_ai_insights(metrics)
            
    except Exception as e:
        # Fallback to local demo insights if it fails
        insights = generate_local_analyst_insights(metrics, is_demo=True, error_msg=str(e))

    # 5. Return complete dashboard package
    return {
        "filename": file.filename,
        "rows_processed": len(df),
        "metrics": metrics,
        "insights": insights
    }
