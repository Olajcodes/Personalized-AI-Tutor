from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel, Field
from typing import List
from neomodel import config
from practice.models.model import Student, Concept, MasteryRel
from dotenv import load_dotenv
import os
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

app = FastAPI(title="Learning Path API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
config.DATABASE_URL = "bolt://neo4j:AjeeNTestDB1!@127.0.0.1:7687"

# --- Request Schemas ---
class MasteryRequest(BaseModel):
    student_id: str = Field(..., example="ajee_01")
    concept_name: str = Field(..., example = "Calculus")
    score: float = Field(..., example = 0.95)
    
# --- The endpoint ---


# 1. Create a Pydantic model to receive the request from React
class GoogleAuthRequest(BaseModel):
    token: str

@app.post("/api/auth/google")
async def verify_google_token(request: GoogleAuthRequest):
    try:
        # 2. Verify the token with Google's servers
        id_info = id_token.verify_oauth2_token(
            id_token=request.token,
            request=requests.Request(),
            audience=GOOGLE_CLIENT_ID
        )

        # 3. Extract the user info! Google gives you all of this:
        email = id_info.get("email")
        first_name = id_info.get("given_name")
        last_name = id_info.get("family_name")
        profile_pic = id_info.get("picture")
        google_id = id_info.get("sub") # Google's unique ID for this user

        # --- 4. DATABASE LOGIC GOES HERE ---
        # user = db.query(User).filter(User.email == email).first()
        # if not user:
        #     user = User(email=email, first_name=first_name, ...)
        #     db.add(user)
        #     db.commit()
        # -----------------------------------

        # 5. Generate your OWN FastAPI JWT token for the session (Placeholder)
        my_backend_token = f"fake-backend-token-for-{email}"
    
        return {
            "message": "Login successful",
            "access_token": my_backend_token,
            "user": {
                "email": email,
                "name": first_name
            }
        }

    except ValueError:
        # If the token is fake, expired, or tampered with, Google throws a ValueError
        raise HTTPException(status_code=401, detail="Invalid Google Token")
    
@app.post("/master-concept")
async def master_concept(request: MasteryRequest):
    # 1. Fetch Student and Concept
    student = Student.nodes.get_or_none(student_id=request.student_id)
    concept = Concept.nodes.get_or_none(name=request.concept_name)
    
    if not student or not concept:
        raise HTTPException(status_code=404, detail="Student or Concept not found")
    
    # 2. Logic: Check Prerequisites
    prereqs = concept.prerequisites.all()
    mastered = student.mastered_concepts.all()
    mastered_names = {c.name for c in mastered}
    
    missing = [p.name for p in prereqs if p.name not in mastered_names]
    
    if missing:
        return {
            "status": "locked",
            "message": f"You must master {missing} first!",
            "missing_prerequisites": missing
        }
    
    # 3. Success: Create or Update the Relationship
    # .relationship() returns the MasteryRel object if it exists
    rel = student.mastered_concepts.relationship(concept)

    if rel:
        # Update existing progress
        rel.score = max(rel.score, request.score) 
        rel.attempts += 1
        rel.save()
        message = f"Progress updated for {concept.name}."
    else:
        # Create new connection
        student.mastered_concepts.connect(concept, {"score": request.score, "attempts": 1})
        message = f"Mastery of {concept.name} recorded!"
    
    return {
        "status": "success", 
        "message": message,
        "current_score": request.score,
        "total_attempts": rel.attempts if rel else 1
    }
    
@app.get("/suggested-concepts/{student_id}")
async def get_suggested_concepts(student_id: str):
    # 1. Fetch the student
    student = Student.nodes.get_or_none(student_id=student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 2. Get names of everything the student has already mastered
    mastered = {c.name for c in student.mastered_concepts.all()}

    # 3. Find available concepts
    all_concepts = Concept.nodes.all()
    suggested = []

    for concept in all_concepts:
        # Skip if already mastered
        if concept.name in mastered:
            continue
        
        # Check prerequisites
        prereqs = concept.prerequisites.all()
        # If no prereqs, OR all prereqs are in the mastered set
        if not prereqs or all(p.name in mastered for p in prereqs):
            suggested.append({
                "name": concept.name,
                "difficulty": concept.difficulty
            })

    return {
        "student_id": student_id,
        "suggested_concepts": suggested,
        "total_ready": len(suggested)
    }