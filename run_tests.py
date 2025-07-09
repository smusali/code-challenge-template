#!/usr/bin/env python3
"""
Comprehensive test runner for Weather Data Engineering API integration tests.

This script provides multiple test execution options:
- Full integration test suite
- Individual test modules
- Performance tests
- Smoke tests
- CI/CD optimized tests

Usage:
    python run_tests.py                    # Run all integration tests
    python run_tests.py --fast            # Run fast tests only
    python run_tests.py --smoke           # Run smoke tests
    python run_tests.py --performance     # Run performance tests
    python run_tests.py --module health   # Run specific test module
    python run_tests.py --coverage        # Run with coverage report
    python run_tests.py --ci              # Run in CI/CD mode
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test configuration
TEST_MODULES = {
    "health": "tests/test_health_endpoints.py",
    "enhanced": "tests/test_enhanced_endpoints.py",
    "documentation": "tests/test_documentation_endpoints.py",
    "weather": "tests/test_weather_endpoints.py",
    "errors": "tests/test_error_scenarios.py",
    "all": "tests/",
}

DEFAULT_PYTEST_ARGS = [
    "-v",  # Verbose output
    "--tb=short",  # Short traceback format
    "--strict-markers",  # Strict marker validation
    "--disable-warnings",  # Disable warnings for cleaner output
]

CI_PYTEST_ARGS = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--disable-warnings",
    "--maxfail=5",  # Stop after 5 failures
    "--durations=10",  # Show 10 slowest tests
]

COVERAGE_ARGS = [
    "--cov=src",
    "--cov=core_django",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-report=xml",
]


class TestRunner:
    """Main test runner class."""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.tests_dir = self.project_root / "tests"
        self.results_dir = self.project_root / "test_results"
        self.coverage_dir = self.project_root / "htmlcov"

        # Ensure directories exist
        self.results_dir.mkdir(exist_ok=True)

    def run_command(self, cmd: list[str], capture_output: bool = False) -> int:
        """Run a command and return the exit code."""
        print(f"Running: {' '.join(cmd)}")

        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error running command: {result.stderr}")
            return result.returncode
        else:
            return subprocess.run(cmd).returncode

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        print("Checking dependencies...")

        required_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-django",
            "httpx",
            "asgi-lifespan",
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            print(f"Missing required packages: {', '.join(missing_packages)}")
            print("Install them with: pip install " + " ".join(missing_packages))
            return False

        print("✓ All dependencies are available")
        return True

    def setup_environment(self) -> None:
        """Set up test environment variables."""
        print("Setting up test environment...")

        # Set environment variables for testing
        os.environ["TESTING"] = "True"
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["DJANGO_SETTINGS_MODULE"] = "core_django.core.settings"
        os.environ["LOG_LEVEL"] = "WARNING"

        # Ensure Django is properly configured
        try:
            import django
            from django.conf import settings

            if not settings.configured:
                django.setup()
        except ImportError:
            print("Warning: Django not available, some tests may fail")

        print("✓ Test environment configured")

    def run_smoke_tests(self) -> int:
        """Run smoke tests (basic functionality)."""
        print("Running smoke tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/test_health_endpoints.py::TestHealthEndpoints::test_health_check_basic",
            "tests/test_health_endpoints.py::TestHealthEndpoints::test_root_endpoint",
            "tests/test_enhanced_endpoints.py::TestEnhancedWeatherStations::test_weather_stations_basic",
            "tests/test_documentation_endpoints.py::TestOpenAPIDocumentation::test_openapi_schema",
        ] + DEFAULT_PYTEST_ARGS

        return self.run_command(cmd)

    def run_fast_tests(self) -> int:
        """Run fast tests (excluding slow tests)."""
        print("Running fast tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/",
            "-m",
            "not slow",
        ] + DEFAULT_PYTEST_ARGS

        return self.run_command(cmd)

    def run_performance_tests(self) -> int:
        """Run performance tests."""
        print("Running performance tests...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/",
            "-m",
            "performance",
        ] + DEFAULT_PYTEST_ARGS

        return self.run_command(cmd)

    def run_module_tests(self, module: str) -> int:
        """Run tests for a specific module."""
        if module not in TEST_MODULES:
            print(f"Unknown module: {module}")
            print(f"Available modules: {', '.join(TEST_MODULES.keys())}")
            return 1

        test_path = TEST_MODULES[module]
        print(f"Running tests for module: {module}")

        cmd = [
            "python",
            "-m",
            "pytest",
            test_path,
        ] + DEFAULT_PYTEST_ARGS

        return self.run_command(cmd)

    def run_all_tests(self, with_coverage: bool = False, ci_mode: bool = False) -> int:
        """Run all integration tests."""
        print("Running all integration tests...")

        pytest_args = CI_PYTEST_ARGS if ci_mode else DEFAULT_PYTEST_ARGS

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/",
        ] + pytest_args

        if with_coverage:
            cmd.extend(COVERAGE_ARGS)

        return self.run_command(cmd)

    def run_with_html_report(self) -> int:
        """Run tests with HTML report generation."""
        print("Running tests with HTML report...")

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/",
            "--html=test_results/report.html",
            "--self-contained-html",
        ] + DEFAULT_PYTEST_ARGS

        return self.run_command(cmd)

    def run_parallel_tests(self, num_workers: int = 4) -> int:
        """Run tests in parallel using pytest-xdist."""
        print(f"Running tests in parallel with {num_workers} workers...")

        try:
            import importlib.util

            if importlib.util.find_spec("pytest_xdist") is None:
                print(
                    "pytest-xdist not available, install with: pip install pytest-xdist"
                )
                return 1
        except ImportError:
            print("pytest-xdist not available, install with: pip install pytest-xdist")
            return 1

        cmd = [
            "python",
            "-m",
            "pytest",
            "tests/",
            "-n",
            str(num_workers),
        ] + DEFAULT_PYTEST_ARGS

        return self.run_command(cmd)

    def generate_coverage_report(self) -> None:
        """Generate coverage report after tests."""
        if self.coverage_dir.exists():
            print(f"Coverage report generated: {self.coverage_dir}/index.html")

        # Print coverage summary
        if (self.project_root / "coverage.xml").exists():
            print("Coverage report saved to coverage.xml")

    def cleanup(self) -> None:
        """Clean up temporary files."""
        temp_files = [
            ".pytest_cache",
            ".coverage",
            "__pycache__",
        ]

        for temp_file in temp_files:
            temp_path = self.project_root / temp_file
            if temp_path.exists():
                if temp_path.is_dir():
                    import shutil

                    shutil.rmtree(temp_path, ignore_errors=True)
                else:
                    temp_path.unlink()

    def print_test_summary(self, exit_code: int, start_time: float) -> None:
        """Print test execution summary."""
        elapsed_time = time.time() - start_time

        print("\n" + "=" * 50)
        print("TEST EXECUTION SUMMARY")
        print("=" * 50)

        if exit_code == 0:
            print("✓ All tests passed successfully!")
        else:
            print(f"✗ Tests failed with exit code: {exit_code}")

        print(f"Execution time: {elapsed_time:.2f} seconds")
        print(f"Test results available in: {self.results_dir}")

        if self.coverage_dir.exists():
            print(f"Coverage report available in: {self.coverage_dir}/index.html")

        print("=" * 50)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Weather Data Engineering API Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_tests.py                    # Run all tests
    python run_tests.py --fast            # Run fast tests only
    python run_tests.py --smoke           # Run smoke tests
    python run_tests.py --performance     # Run performance tests
    python run_tests.py --module health   # Run health endpoint tests
    python run_tests.py --coverage        # Run with coverage
    python run_tests.py --ci              # Run in CI mode
    python run_tests.py --parallel 4      # Run with 4 parallel workers
        """,
    )

    parser.add_argument(
        "--fast", action="store_true", help="Run fast tests only (exclude slow tests)"
    )

    parser.add_argument(
        "--smoke", action="store_true", help="Run smoke tests (basic functionality)"
    )

    parser.add_argument(
        "--performance", action="store_true", help="Run performance tests only"
    )

    parser.add_argument(
        "--module",
        choices=list(TEST_MODULES.keys()),
        help="Run tests for specific module",
    )

    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage report"
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run in CI/CD mode (optimized for automated testing)",
    )

    parser.add_argument(
        "--parallel", type=int, metavar="N", help="Run tests in parallel with N workers"
    )

    parser.add_argument(
        "--html-report", action="store_true", help="Generate HTML test report"
    )

    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up temporary files and exit"
    )

    args = parser.parse_args()

    # Initialize test runner
    runner = TestRunner()

    # Handle cleanup
    if args.cleanup:
        runner.cleanup()
        print("Cleanup completed")
        return 0

    # Check dependencies
    if not runner.check_dependencies():
        return 1

    # Setup environment
    runner.setup_environment()

    # Record start time
    start_time = time.time()

    # Run tests based on arguments
    exit_code = 0

    try:
        if args.smoke:
            exit_code = runner.run_smoke_tests()
        elif args.fast:
            exit_code = runner.run_fast_tests()
        elif args.performance:
            exit_code = runner.run_performance_tests()
        elif args.module:
            exit_code = runner.run_module_tests(args.module)
        elif args.parallel:
            exit_code = runner.run_parallel_tests(args.parallel)
        elif args.html_report:
            exit_code = runner.run_with_html_report()
        else:
            exit_code = runner.run_all_tests(
                with_coverage=args.coverage, ci_mode=args.ci
            )

        # Generate coverage report if requested
        if args.coverage:
            runner.generate_coverage_report()

    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        exit_code = 130

    except Exception as e:
        print(f"Error during test execution: {e}")
        exit_code = 1

    finally:
        # Print summary
        runner.print_test_summary(exit_code, start_time)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
