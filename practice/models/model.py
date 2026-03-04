from neomodel import StructuredNode, StringProperty, IntegerProperty, DateTimeProperty, StructuredRel, FloatProperty, RelationshipTo


class MasteryRel(StructuredRel):
    score = FloatProperty(default=0.0)
    attempts = IntegerProperty(default=1)
    last_reviewed = DateTimeProperty(default_now=True)
    
    

class Student(StructuredNode):
    # Unique identifier for the student
    
    student_id = StringProperty(unique_index = True, required=True)
    name = StringProperty(required=True)
    joined_at = DateTimeProperty(default_now=True)
    
    #This says: "A student can have a MASTERED relationship to a concept"
    mastered_concepts = RelationshipTo('Concept', "MASTERED", model=MasteryRel)
    
class Concept(StructuredNode):
    # Unique name for the cokncept (e.g. "Linear Algebra")
    name = StringProperty(unique_index = True, required=True)
    # Scale of 1-10
    difficulty = IntegerProperty(default=1)
    
    #This allows you to chain concepts: (Linear Algebra) - [:REQUIRES] - > (Calculus)
    
    prerequisites = RelationshipTo('Concept', 'REQUIRES')
    