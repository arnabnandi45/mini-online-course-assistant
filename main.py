from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(title="Mini Online Course Assistant")


# --------------------------------------------------
# Request Model
# --------------------------------------------------

class QuestionRequest(BaseModel):
    question: str


# --------------------------------------------------
# Course Data
# --------------------------------------------------

COURSES = [
    {
        "id": 1,
        "title": "Python Programming",
        "fee": 5000,
        "instructor": "Somenath Singha",
        "details": {
            "level": "Beginner",
            "duration": "3 months",
            "language": "English",
            "tools": ["Python", "PostgreSQL", "FastAPI"]
        }
    },
    {
        "id": 2,
        "title": "Java Programming",
        "fee": 6000,
        "instructor": "Arpita Roy",
        "details": {
            "level": "Intermediate",
            "duration": "4 months",
            "language": "English",
            "tools": ["Java", "MySQL", "DSA"]
        }
    },
    {
        "id": 3,
        "title": "Data Science",
        "fee": 8000,
        "instructor": "Ipshita Saha",
        "details": {
            "level": "Advanced",
            "duration": "6 months",
            "language": "English",
            "tools": ["Python", "Pandas", "NumPy"]
        }
    }
]


# --------------------------------------------------
# Helper: Prepare searchable course information
# --------------------------------------------------

def get_searchable_words(course):
    searchable_text = (
        str(course["title"]) + " "
        + str(course["fee"]) + " "
        + str(course["instructor"]) + " "
        + str(course["details"]["level"]) + " "
        + str(course["details"]["duration"]) + " "
        + str(course["details"]["language"]) + " "
        + " ".join(course["details"]["tools"])
    )

    return searchable_text.lower().split()


# --------------------------------------------------
# Find Best Course
# --------------------------------------------------

def find_best_course(question):

    # Convert question to lowercase
    question = question.lower()

    # Remove simple punctuation
    for symbol in [".", ",", "?", "!"]:
        question = question.replace(symbol, "")

    # Split question into words
    words = question.split()

    best_course = None
    best_score = 0
    best_matched_keywords = []

    # Search every course
    for course in COURSES:

        searchable_words = get_searchable_words(course)

        score = 0
        matched_keywords = []

        # Give one point for every matching question word
        for word in words:

            if word in searchable_words:
                score += 1

                if word not in matched_keywords:
                    matched_keywords.append(word)

        # Keep the course with the highest score
        if score > best_score:
            best_score = score
            best_course = course
            best_matched_keywords = matched_keywords

    return best_course, best_matched_keywords, best_score


# --------------------------------------------------
# Build Grounded Answer
# --------------------------------------------------

def build_answer(course):

    if course is None:
        return "Information not available in the supplied course data."

    title = course["title"]
    level = course["details"]["level"]
    instructor = course["instructor"]
    duration = course["details"]["duration"]
    fee = course["fee"]
    tools = ", ".join(course["details"]["tools"])

    answer = (
        f"{title} is a {level} course taught by {instructor}. "
        f"Its duration is {duration}, its fee is {fee}, "
        f"and its tools include {tools}."
    )

    return answer


# --------------------------------------------------
# Build Prompt Preview
# --------------------------------------------------

def build_prompt(question, course):

    if course is None:
        return None

    context = (
        f"Title: {course['title']}\n"
        f"Fee: {course['fee']}\n"
        f"Instructor: {course['instructor']}\n"
        f"Level: {course['details']['level']}\n"
        f"Duration: {course['details']['duration']}\n"
        f"Language: {course['details']['language']}\n"
        f"Tools: {', '.join(course['details']['tools'])}"
    )

    prompt = f"""ROLE
You are an online course assistant.

RULES
Use only the supplied course information.
Do not guess or invent information.

CONTEXT
{context}

QUESTION
{question}
"""

    return prompt


# --------------------------------------------------
# GET /courses
# --------------------------------------------------

@app.get("/courses")
def get_courses():
    return COURSES


# --------------------------------------------------
# GET /courses/{course_id}
# --------------------------------------------------

@app.get("/courses/{course_id}")
def get_course(course_id: int):

    for course in COURSES:

        if course["id"] == course_id:
            return course

    raise HTTPException(
        status_code=404,
        detail="Course not found"
    )


# --------------------------------------------------
# POST /ask
# --------------------------------------------------

@app.post("/ask")
def ask_question(request: QuestionRequest):

    # Check empty question
    if not request.question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    # Find best course
    course, matched_keywords, match_score = find_best_course(
        request.question
    )

    # No matching course
    if course is None:

        return {
            "question": request.question,
            "retrieved_course": None,
            "matched_keywords": [],
            "match_score": 0,
            "answer": "Information not available in the supplied course data.",
            "source": None,
            "prompt_preview": None
        }

    # Build answer
    answer = build_answer(course)

    # Build prompt preview
    prompt_preview = build_prompt(
        request.question,
        course
    )

    return {
        "question": request.question,
        "retrieved_course": course["title"],
        "matched_keywords": matched_keywords,
        "match_score": match_score,
        "answer": answer,
        "source": course["title"],
        "prompt_preview": prompt_preview
    }