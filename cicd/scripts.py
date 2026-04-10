"""This module contains scripts for quality assurance check and deployment."""

import argparse
import os
import sys
import subprocess
from dotenv import load_dotenv


# ========== Quality Assurance Checks ==========
def code_lint():
    """Run pylint, isort, and black for checking and linting the code."""
    print("🚀 Linter checks are in progress...")
    linter_commands = [
        ["isort", "--check", "src/"],
        ["black", "--check", "src/"],
        ["pylint", "src/"],
    ]
    for lint in linter_commands:
        try:
            print(f"🔄 Checking with {lint[0]}.")
            result = subprocess.run(lint, check=True)
        except Exception as err:
            print("\n❌ Linter failed!\nCheck & fix the linter's output.\n")
            sys.exit(-1)
    print("✅ Linter checks are done.\n", 50 * "=")


def code_format():
    """Run black and isort to format the code."""
    print("🚀 Formatting the code is in progress...")
    format_commands = [
        ["isort", "src/"],
        ["black", "src/"],
    ]
    for format in format_commands:
        try:
            print(f"🔄 Formatting with {format[0]}.")
            result = subprocess.run(format, check=True)
        except Exception as err:
            print("\n❌ Formatting failed!\nCheck the formatter's output to fix the issue.\n")
            sys.exit(-1)
    print("✅ Formattings are done.\n", 50 * "=")


def run_tests():
    """Run pytest to execute the tests."""
    print("🚀 Running tests is in progress...")
    try:
        result = subprocess.run(["pytest", "tests/"], check=True)
    except Exception as err:
        print("\n❌ Tests failed!\nCheck the test output to fix the issue.\n")
        sys.exit(-1)
    print("✅ All unit tests are passed.\n", 50 * "=")


def pre_commit():
    """Running checks to ensure quality software before code commit and push."""
    code_format()
    code_lint()
    run_tests()


# ========= Running the services ==========
def run_backend():
    """Run the backend services, including SQL database, Vector database, and ChatEngine API."""
    print("🚀 Running the backend service is in progress...")
    try:
        result = subprocess.run(["docker", "compose", "--env-file", ".env", "up"], check=True)
    except Exception as err:
        print("\n❌ Backend run failed!\nCheck the run output to fix the issue.\n")
        sys.exit(-1)
    print("✅ Backend services are running.")


def run_frontend():
    """Run the Streamlit UI frontend service."""
    print("🚀 Starting the Streamlit UI...")
    try:
        # result = subprocess.run(["docker-compose", "up", "-d", "frontend"], check=True)
        result = subprocess.run(["streamlit", "run", "src/ui/app.py"], check=True)
    except Exception as err:
        print("\n❌ Starting the Streamlit UI failed!\nCheck the run output to fix the issue.\n")
        sys.exit(-1)
    print("✅ Streamlit UI is running.")


# ========= Running evaluation tests ==========
def performance_test():
    """Run the performance test script."""
    print("🚀 Running performance tests...")
    try:
        result = subprocess.run(["python", "tests/performance_test.py"], check=True)
    except Exception as err:
        print("\n❌ Performance tests failed!\nCheck the test output to fix the issue.\n")
        sys.exit(-1)
    print("✅ Performance tests passed.")


def accuracy_test():
    """Run the accuracy test script."""
    print("🚀 Running accuracy tests...")
    try:
        result = subprocess.run(["python", "tests/accuracy_test.py"], check=True)
    except Exception as err:
        print("\n❌ Accuracy tests failed!\nCheck the test output to fix the issue.\n")
        sys.exit(-1)
    print("✅ Accuracy tests passed.")


if __name__ == "__main__":
    pre_commit()