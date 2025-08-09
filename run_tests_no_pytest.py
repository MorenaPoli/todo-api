"""
A simple script to run basic tests on the FastAPI application defined in `main.py`
without relying on pytest. This script replicates the assertions from
`test_main.py` and prints the outcome of each test as PASS or FAIL.

To run the tests, execute:

    python run_tests_no_pytest.py

The script uses FastAPI's TestClient from httpx under the hood to perform
HTTP requests against the application. If any assertion fails, it will
capture the exception and report the failure, continuing with subsequent
tests.
"""

from fastapi.testclient import TestClient
import os
import sqlite3
import traceback

from main import app, init_db, DB as ORIGINAL_DB

# Use a dedicated test database file to avoid interfering with the real DB
TEST_DB = "test_todo_run_script.db"


def setup_module() -> None:
    """Prepare the environment for testing.

    Sets the global DB path in the imported module to use the test database
    file and calls `init_db()` to ensure tables are created. If a test
    database already exists, it is removed before initialization.
    """
    # Ensure any existing test database is removed
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass  # ignore if cannot remove; will be overwritten
    # Override the DB path used by the FastAPI app
    import main
    main.DB = TEST_DB
    # Initialize the test DB
    init_db()


def teardown_module() -> None:
    """Clean up after tests have run by removing the test database file."""
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass


def run_tests() -> None:
    """Run the suite of tests defined based on `test_main.py`.

    Each test is executed in order, and results are printed to stdout.
    """
    setup_module()
    client = TestClient(app)
    failures = 0

    def assert_true(condition: bool, message: str) -> None:
        nonlocal failures
        if not condition:
            failures += 1
            print(f"FAIL: {message}")
        else:
            print(f"PASS: {message}")

    # Test root endpoint
    try:
        response = client.get("/")
        assert_true(response.status_code == 200, "root returns status 200")
        assert_true(
            "Todo API is running" in response.json().get("message", ""),
            "root message contains 'Todo API is running'",
        )
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in root endpoint test")
        traceback.print_exc()

    # Test get empty tasks
    try:
        response = client.get("/tasks")
        assert_true(response.status_code == 200, "get empty tasks status code 200")
        assert_true(response.json() == [], "get empty tasks returns empty list")
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in get empty tasks test")
        traceback.print_exc()

    # Test create task
    try:
        task_data = {"title": "Test task", "done": False}
        response = client.post("/tasks", json=task_data)
        assert_true(response.status_code == 200, "create task returns status 200")
        data = response.json()
        assert_true(data.get("title") == "Test task", "create task returns correct title")
        assert_true(data.get("done") is False, "create task returns correct done flag")
        assert_true(data.get("id") == 1, "create task id is 1")
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in create task test")
        traceback.print_exc()

    # Test get tasks with data
    try:
        response = client.get("/tasks")
        assert_true(response.status_code == 200, "get tasks with data status code 200")
        tasks = response.json()
        assert_true(len(tasks) == 1, "get tasks with data returns one task")
        assert_true(tasks[0].get("title") == "Test task", "task title matches after creation")
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in get tasks with data test")
        traceback.print_exc()

    # Test create multiple tasks
    try:
        tasks_to_create = [
            {"title": "Second task", "done": False},
            {"title": "Third task", "done": True},
        ]
        for i, task in enumerate(tasks_to_create, 2):
            response = client.post("/tasks", json=task)
            assert_true(
                response.status_code == 200,
                f"create multiple task {i} returns status 200",
            )
            assert_true(
                response.json().get("id") == i,
                f"task {i} assigned correct id",
            )
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in create multiple tasks test")
        traceback.print_exc()

    # Test update task
    try:
        updated_task = {"title": "Updated task", "done": True}
        response = client.put("/tasks/1", json=updated_task)
        assert_true(response.status_code == 200, "update task returns status 200")
        data = response.json()
        assert_true(data.get("title") == "Updated task", "updated task title correct")
        assert_true(data.get("done") is True, "updated task done flag correct")
        assert_true(data.get("id") == 1, "updated task id correct")
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in update task test")
        traceback.print_exc()

    # Test update nonexistent task
    try:
        task_data = {"title": "Should fail", "done": False}
        response = client.put("/tasks/999", json=task_data)
        assert_true(response.status_code == 404, "update nonexistent task returns 404")
        assert_true(
            "Task not found" in response.json().get("detail", ""),
            "update nonexistent task returns correct error message",
        )
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in update nonexistent task test")
        traceback.print_exc()

    # Test delete task
    try:
        response = client.delete("/tasks/2")
        assert_true(response.status_code == 200, "delete task returns status 200")
        assert_true(
            "deleted successfully" in response.json().get("message", ""),
            "delete task message contains 'deleted successfully'",
        )
        # Verify deletion
        response = client.get("/tasks")
        tasks = response.json()
        task_ids = [task.get("id") for task in tasks]
        assert_true(2 not in task_ids, "deleted task id 2 is not present")
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in delete task test")
        traceback.print_exc()

    # Test delete nonexistent task
    try:
        response = client.delete("/tasks/999")
        assert_true(response.status_code == 404, "delete nonexistent task returns 404")
        assert_true(
            "Task not found" in response.json().get("detail", ""),
            "delete nonexistent task returns correct error message",
        )
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in delete nonexistent task test")
        traceback.print_exc()

    # Test create task validation
    try:
        # Without title should return 422 (validation error)
        response = client.post("/tasks", json={"done": False})
        assert_true(
            response.status_code == 422,
            "create task without title returns 422",
        )
        # Empty title string is allowed and returns 200
        response = client.post("/tasks", json={"title": "", "done": False})
        assert_true(
            response.status_code == 200,
            "create task with empty title returns 200",
        )
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in create task validation test")
        traceback.print_exc()

    # Test final tasks count
    try:
        response = client.get("/tasks")
        assert_true(response.status_code == 200, "final tasks count status 200")
        tasks = response.json()
        # After creating 3 tasks initially + 1 from validation and deleting 1, expect 3 tasks left
        assert_true(
            len(tasks) == 3,
            "final tasks count is 3 after operations",
        )
        task_ids = [task.get("id") for task in tasks]
        assert_true(
            2 not in task_ids,
            "final tasks list does not contain deleted id 2",
        )
    except Exception:
        failures += 1
        print("FAIL: Exception occurred in final tasks count test")
        traceback.print_exc()

    teardown_module()
    if failures == 0:
        print("\nAll tests passed successfully!")
    else:
        print(f"\n{failures} test(s) failed.")


if __name__ == "__main__":
    run_tests()