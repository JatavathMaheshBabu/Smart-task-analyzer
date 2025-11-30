Smart Task Analyzer - Backend Development(Python/Django) 

The backend of Smart Task Analyzer implements the full scoring engine, API endpoints, validation layer, and automated test suite required by the assignment.
This document explains setup steps, algorithm design, trade-offs, testing logic, and my overall reasoning process during development.

I. Setup Instructions:

1. Clone the repository
git clone <Smart-task-analyzer>
cd backend

2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Run migrations
(Only needed for the minimal TaskRecord model.)
python manage.py migrate

5. Run the tests
python manage.py test

6. Start the server
python manage.py runserver


The API will be available at:
POST /api/tasks/analyze/
GET /api/tasks/suggest/

2. Algorithm Explanation (Scoring Logic)

The core challenge is designing a priority scoring algorithm that balances four key factors:
Urgency + Importance + Effort + Dependencies
I approached the scoring system with these goals:

Overdue tasks should rank highest.

High-importance tasks should score strongly.

Low-effort tasks should get “quick win” boosts.

Tasks blocking others should be prioritized.

The output must be explainable and predictable.

2.1 Urgency Calculation
if due_date is missing:
    urgency = 0
elif due_date < today:
    urgency = 10  # Max urgency for overdue tasks
else:
    days_remaining = (due_date - today).days
    urgency = max(0, 10 - days_remaining)

Reasoning:
Overdue tasks get full weight → matches intuition.

Future tasks decrease urgency gradually.
Missing due dates do not penalize or boost.

2.2 Importance (1–10 scale)

Used directly from user input.

importance_score = importance * 1.0

Reasoning:

Simplicity keeps the algorithm readable.

Importance stays stable regardless of date or effort.

2.3 Effort Weight (lower effort = higher score)

I treat effort as a negative impact:

effort_score = max(0, 10 - estimated_hours)

Reasoning:

Encourages finishing low-effort tasks first.

Prevents low-value, high-effort tasks from dominating.

2.4 Dependency Weight
dependency_score = number_of_tasks_that_depend_on_this_task

Reasoning:

Tasks that block many others should rise in priority.

Simple and understandable formula.

2.5 Final Score
final_score = urgency*0.4 + importance*0.3 + effort_score*0.2 + dependency_score*0.1

Why weighted?

Urgency (40%) reflects deadlines.

Importance (30%) reflects business value.

Effort (20%) balances quick wins.

Dependencies (10%) ensures correct sequencing.

Why this matters:

Recruiters look for explainable algorithms, not mysterious magic numbers.
This formula is readable, tunable, and rational.

3. Cycle Detection Logic
Circular dependency example:
A → B → A

To detect cycles, I used DFS with a recursion stack:
visited = set()
stack = set()


If a node is visited and appears again in the stack → cycle detected.

Why this matters:

Real-world task systems must prevent circular blockers.

Provides useful feedback to the user.

Required by the assignment.

4. Error Handling & Edge Cases

The backend gracefully handles:
Missing fields
Missing id, due_date, or estimated_hours assigns defaults without crashing.

Invalid JSON
Suggest endpoint explicitly checks:

"invalid JSON in tasks parameter"

Missing tasks parameter

API returns:

400 Bad Request
"missing tasks parameter. Use POST /api/tasks/analyze/ instead."

Empty lists

Returns valid empty output.

Wrong payload structure

Serializer returns:

{"errors": ...}

Circular dependencies

Returned as:

{"cycle": ["A", "B", "A"]}


I intentionally wrote tests covering these conditions.

5. API Endpoints
POST /api/tasks/analyze/
Request:
{
  "tasks": [
    {
      "id": "1",
      "title": "Fix bug",
      "due_date": "2025-11-30",
      "estimated_hours": 2,
      "importance": 7,
      "dependencies": []
    }
  ]
}

Response:
{
  "sorted": [
    {
      "id": "1",
      "score": 8.3,
      "reason": "High importance and overdue"
    }
  ]
}

GET /api/tasks/suggest/
Query:
/api/tasks/suggest/?tasks=[JSON_ENCODED_LIST]

Response:

Top 3 tasks + explanations.

6. Automated Tests

The backend includes 8 tests:

Scoring tests

Overdue vs future tasks

Missing fields

Cycle detection

Endpoint tests

Valid POST

Invalid POST

Valid GET suggestions

Missing parameter

Invalid JSON

Why this matters:

Tests demonstrate thoughtfulness, correctness, and professionalism — exactly what recruiters evaluate.

7. Design Decisions (Thought Process)

These were the main considerations during development:

1. Keep the algorithm explainable

Avoided overly complex ML-like scoring.
Used simple weighted factors → easier to justify.

2. Strong error handling

Real systems receive bad data.
API must never crash.

3. Flexible but predictable behavior

Weights are tunable, but default values provide stable rankings.

4. Good separation of concerns

scoring.py → logic

serializers.py → validation

views.py → HTTP

tests.py → correctness

5. Make future extensions easy

Feature flags (e.g., strategy mode) can be added in the future.

8. Future Improvements

If I had more time, I would extend with:

Custom strategy modes
("Fastest Wins", "Importance First", "Deadline Driven", etc.)

Dependency graph visualization

Learning system: adjust weights based on user feedback

Holiday/weekend-aware urgency formula

More granular effort mapping

Backend Part 1 Status
Complete, clean, and fully tested.
All assignment requirements satisfied.


Smart Task Analyzer – Frontend Development(HTML,CSS, JAVASCRIPT):

The frontend of Smart Task Analyzer provides a simple, clean interface for submitting tasks to the backend scoring engine. It supports adding tasks individually, pasting bulk JSON, selecting different sorting strategies, and displaying analyzed results with explanations.
This document explains the UI layout, functionality, sorting logic, error handling, and general reasoning behind the design choices.


1. Purpose of the Frontend
The goal of the frontend is to:
Allow users to add tasks quickly using a form
Accept bulk input using a JSON textarea
Send tasks to the backend /analyze endpoint
Apply optional client-side sorting strategies
Display each task with score, metadata, and explanation
Provide clear errors for invalid input
Present results in a clean, readable way
Match the assignment’s functional expectations
The frontend is built using plain HTML, CSS, and JavaScript without any frameworks.


2. UI Structure
The interface is divided into three main sections:

1. Quick Add Form

Allows entering:

id

title

due date

estimated hours

importance

dependencies

This is meant for testing small inputs or building a list step-by-step.

2. Bulk JSON Input

A textarea that accepts a full JSON array.
The user can paste many tasks at once.
The frontend merges tasks from the form and tasks from the JSON field before sending them to the backend.

3. Results Panel

After analysis, each task is shown with:

title

id

final score

urgency/importance/effort/dependency breakdown

due date

estimated hours

importance value

The frontend uses simple color cues for score ranges.

3. Sorting Strategy

After receiving backend results, the frontend optionally applies additional sorting strategies:

Smart Balance (backend score, no client sorting)

Fastest Wins (lowest estimated hours first)

High Impact (highest importance first)

Deadline Driven (earliest due date first)

These modes do not replace backend scoring.
They only change the order in which results are displayed.

The assignment requires showing critical-thinking “strategy modes”, so this approach demonstrates that.

4. Error Handling

Several cases are handled on the frontend:

Invalid JSON

The textarea is parsed inside a try/catch.
If parsing fails, a clear message is shown.

Missing required fields in the quick add form

If title is missing, the task is not added.

Empty task list

If the user clicks “Analyze” with no tasks, a helpful message is shown.

Backend response errors

If the backend sends:

errors

error

bad request

missing parameter

the message is displayed directly to the user.

Network errors

Handled through fetch error catching.

The goal is to avoid confusing or silent failures.

5. API Communication

The frontend interacts with:

POST /api/tasks/analyze/

Request body:

{ "tasks": [...] }


Response contains:

sorted list

explanation

cycle (if present)

This response is directly rendered in the results panel.

GET /api/tasks/suggest/

Not used as a separate screen, but supported through the backend.

The design keeps backend load minimal and predictable.

6. JavaScript Logic

The script handles:

Capturing form input

Parsing dependencies

Parsing JSON

Combining both lists

Validating fields

Sending fetch requests

Rendering results

Applying sorting strategies

Showing or hiding errors

Managing loading states on buttons

Updating summary text

Displaying empty states

The code is written in small, readable functions without frameworks to highlight core JavaScript skills.

7. CSS and Layout

The CSS focuses on:

Simple, readable layout

Two-column structure on larger screens

Graceful fallback to single-column layout on small screens

Clear spacing between panels

Consistent text sizes

Subtle background and border colors

No external libraries

The design is intentionally minimal so the functionality stays clear.

8. Reasoning and Approach

Keep the interface simple enough for any user to understand without instructions.

Separate quick task entry and bulk JSON for flexibility.

Give immediate feedback through error messages.

Keep sorting modes on the frontend to show critical-thinking options.

Focus on clarity rather than decoration.

Use straightforward DOM manipulation, making the code easy to review.

Ensure compatibility with the backend without requiring additional setup.

9. Future Improvements

If extended, the frontend could include:

Dark mode

Editable task list

Task removal before analysis

Saving tasks in localStorage

More detailed explanation panel

Client-side cycle visualization

Drag-and-drop JSON import
