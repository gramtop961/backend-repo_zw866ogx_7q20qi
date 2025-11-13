import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Service, Inquiry

app = FastAPI(title="E-commerce Site API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class ObjectIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        try:
            return str(ObjectId(v))
        except Exception as e:
            raise ValueError("Invalid ObjectId")


class ProductResponse(Product):
    id: Optional[ObjectIdStr] = None


class ServiceResponse(Service):
    id: Optional[ObjectIdStr] = None


class InquiryRequest(Inquiry):
    pass


@app.get("/")
async def root():
    return {"message": "E-commerce API is running"}


@app.get("/api/products", response_model=List[ProductResponse])
async def list_products():
    try:
        docs = get_documents("product")
        # map _id -> id as string
        out = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
            out.append(d)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/inquiry")
async def create_inquiry(payload: InquiryRequest):
    try:
        _id = create_document("inquiry", payload)
        return {"status": "ok", "id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/services", response_model=List[ServiceResponse])
async def list_services():
    try:
        docs = get_documents("service")
        out = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
            out.append(d)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
