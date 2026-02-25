from neomodel import config
from models.model import Student, Concept

# Update with your verified credentials
config.DATABASE_URL = "bolt://neo4j:AjeeNTestDB1!@127.0.0.1:7687"

def setup():
    print("🌱 Populating Knowledge Graph...")

    # 1. Create a Student
    ajee = Student.get_or_create({"student_id": "ajee_01", "name": "Ajee"})[0]

    # 2. Create Concepts
    algebra = Concept.get_or_create({"name": "Algebra", "difficulty": 2})[0]
    calculus = Concept.get_or_create({"name": "Calculus", "difficulty": 5})[0]

    # 3. Define a Prerequisite (Calculus requires Algebra)
    if not calculus.prerequisites.is_connected(algebra):
        calculus.prerequisites.connect(algebra)
        print("🔗 Linked: Calculus -> requires -> Algebra")

    print("✅ Setup complete! You now have a student and a learning path.")

if __name__ == "__main__":
    setup()