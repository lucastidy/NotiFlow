"""
Flask API Backend for NotiFlow

Provides REST endpoints for retrieving Canvas-related academic data,
including:
  - course lists
  - final exam schedules
  - announcements
  - assignment metadata

The backend communicates with Canvas through helper modules:
  - assignment_feature.AssignmentFetcher
  - final_exam_feature.FinalExam
  - announcement_feature.announcement_main
  - iCalBackendNew.ICalHandler

All endpoints return JSON and support CORS to allow access from the Chrome extension.
Runs on localhost:8080 during development.

Routes:
  GET /api/courses        → returns list of courses
  GET /api/finalexam      → returns final exam information
  GET /api/announcements  → returns announcement data
  GET /api/assignments    → returns assignment grouping by course
"""
try: # relative import if run as module
    from announcement_feature.announcement_main import main as announcement_main
except ModuleNotFoundError: # absolute import if run as script
    from Backend.announcement_feature.announcement_main import main as announcement_main

try: # relative import if run as module
    from assignment_feature.AssignmentFetcher import mapCourses, getClasses
except ModuleNotFoundError: # absolute import if run as script
    from Backend.assignment_feature.AssignmentFetcher import mapCourses, getClasses

# from final_exam_feature.FinalExam import *
try: # relative import if run as module
    from final_exam_feature.FinalExam import FinalExamFetcher as fe
except ModuleNotFoundError: # absolute import if run as script
    from Backend.final_exam_feature.FinalExam import FinalExamFetcher as fe
from flask import Flask, jsonify, request
from flask_cors import CORS
try: # relative import if run as module
    from iCalBackendNew import ICalHandler
except ModuleNotFoundError: # absolute import if run as script
    from Backend.iCalBackendNew import ICalHandler

app = Flask(__name__)
cors = CORS(app, origins="*")

"""
GET /api/courses

Retrieves the course list for a given Canvas API token.

Query Params:
  - token (string): Canvas API token needed to authenticate the request.

Process:
  1. Extracts token from the query string.
  2. Calls getClasses(token) to fetch course metadata.
  3. Returns the result as JSON.

Returns:
  JSON list of course objects.
"""
@app.route("/api/courses", methods=["GET"])
def classes():
    token = request.args.get("token")
    courses = getClasses(token)
    return jsonify(courses)

"""
GET /api/finalexam

Retrieves final exam information for a list of course IDs.

Query Params:
  - course[] (list[str]): A repeated query parameter representing course identifiers.

Process:
  1. Reads all course[] parameters into a list.
  2. Calls FinalExamFetcher.get_finals(courses) to fetch exam data.
  3. Passes the exam data into ICalHandler to generate an .ics calendar file.
  4. Returns the exam data as JSON.

Returns:
  JSON list containing final exam schedules for the provided courses.
"""
@app.route("/api/finalexam", methods=["GET"])
def finalexam():
    courses = request.args.getlist("course[]")
    token = request.args.getlist("token")
    print(courses)
    finals_response = fe.get_finals(courses)  # FIXME verify
    print(finals_response)
    handler = ICalHandler(token)
    handler.process_json(finals_response)
    handler.save_calendar()
    return jsonify(finals_response)
    # courses = request.args.getlist("course[]")
    # finals = fe.get_finals(courses)
    # # handler = ICalHandler()
    # # handler.process_json(finals_response)
    # # handler.save_calendar()
    # return jsonify(finals)

"""
GET /api/announcements

Fetches Canvas announcements for the authenticated user.

Query Params:
  - token (string): Canvas API token.

Process:
  1. Reads token from query string.
  2. Uses announcement_main(token) to retrieve announcement data.
  3. Sends the data through ICalHandler to create an .ics calendar file.
  4. Returns announcement JSON.
  5. On failure, returns an error object with status 500.

Returns:
  JSON announcement data or an error response.
"""
@app.route("/api/announcements", methods=["GET"])
def announcements():
    try:
        token = request.args.get("token")
        handler = ICalHandler(token)
        ann = announcement_main(token)
        handler.process_json(ann)
        handler.save_calendar()
        return ann
    except Exception as e:
        return jsonify({"error": str(e)}), 500

"""
GET /api/assignments

Fetches assignment data grouped by course.

Query Params:
  - token (string): Canvas API token.

Process:
  1. Extracts token from query parameters.
  2. Calls mapCourses(token) from AssignmentFetcher to retrieve assignments.
  3. Returns grouped assignment data as JSON.
  4. Returns JSON error object on exception.

Returns:
  JSON object mapping courses to assignment lists.
"""
@app.route("/api/assignments", methods=["GET"])
def assignments():
    try:
        token = request.args.get("token")
        print("Received token:", token)
        handler = ICalHandler(token)
        assignments = mapCourses(token)
        handler.process_assignments(assignments)
        handler.save_calendar()
        return assignments
    except Exception as e:
        return jsonify({"error": str(e)}), 500


"""
Development entry point.

Runs the Flask application on localhost:8080 with debug mode enabled.
"""
if __name__ == "__main__":
    app.run(debug=True, port=8080)
