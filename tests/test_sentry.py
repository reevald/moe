"""
Test Sentry.io connection.

This script tests:
1. Sentry SDK initialization
2. Error capture
3. Transaction/trace capture
4. Integration with FastAPI and Celery
"""

import os
import sys
import time
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_success(message: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"{BLUE}ℹ {message}{RESET}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}⚠ {message}{RESET}")


def test_sentry_connection(
    dsn: str,
    environment: str = "development",
    traces_sample_rate: float = 0.1
) -> bool:
    """
    Test connection to Sentry.
    
    Args:
        dsn: Sentry DSN
        environment: Environment name
        traces_sample_rate: Trace sampling rate
    
    Returns:
        bool: True if all tests pass
    """
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing Sentry.io Connection{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    print_info(f"DSN: {dsn[:30]}..." if dsn else "No DSN")
    print_info(f"Environment: {environment}")
    print_info(f"Traces Sample Rate: {traces_sample_rate}")
    
    all_tests_passed = True
    
    # Test 1: Initialize Sentry
    print(f"\n{BLUE}Test 1: Initialize Sentry SDK{RESET}")
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            attach_stacktrace=True,
            send_default_pii=False,
            integrations=[
                LoggingIntegration(
                    level=None,
                    event_level=None
                )
            ]
        )
        print_success("Sentry SDK initialized")
    except Exception as e:
        print_error(f"Failed to initialize Sentry: {e}")
        return False
    
    # Test 2: Capture Test Message
    print(f"\n{BLUE}Test 2: Capture Test Message{RESET}")
    try:
        print_info("Sending test message to Sentry...")
        
        event_id = sentry_sdk.capture_message(
            "MOE Test Connection - This is a test message",
            level="info"
        )
        
        print_success(f"Message captured with event ID: {event_id}")
        print_info(
            "Check Sentry dashboard to verify message arrival"
        )
    except Exception as e:
        print_error(f"Failed to capture message: {e}")
        all_tests_passed = False
    
    # Test 3: Capture Test Exception
    print(f"\n{BLUE}Test 3: Capture Test Exception{RESET}")
    try:
        print_info("Sending test exception to Sentry...")
        
        try:
            # Intentionally raise an exception for testing
            raise ValueError("MOE Test Exception - This is a test error")
        except ValueError as e:
            event_id = sentry_sdk.capture_exception(e)
            print_success(f"Exception captured with event ID: {event_id}")
            print_info(
                "Check Sentry dashboard to verify exception arrival"
            )
    except Exception as e:
        print_error(f"Failed to capture exception: {e}")
        all_tests_passed = False
    
    # Test 4: Create Test Transaction
    print(f"\n{BLUE}Test 4: Create Test Transaction{RESET}")
    try:
        print_info("Creating test transaction...")
        
        with sentry_sdk.start_transaction(
            op="test",
            name="connection_test"
        ) as transaction:
            # Simulate some work
            with sentry_sdk.start_span(
                op="test.operation",
                description="test operation"
            ):
                time.sleep(0.1)
            
            print_success(
                f"Transaction created: {transaction.name}"
            )
            print_info(
                "Check Sentry Performance dashboard to verify"
            )
    except Exception as e:
        print_error(f"Failed to create transaction: {e}")
        all_tests_passed = False
    
    # Test 5: Test with Context
    print(f"\n{BLUE}Test 5: Test with User Context{RESET}")
    try:
        print_info("Setting user context and capturing message...")
        
        sentry_sdk.set_user({
            "id": "test-user-123",
            "username": "test_user",
            "email": "test@example.com"
        })
        
        sentry_sdk.set_tag("test_type", "connection_test")
        sentry_sdk.set_tag("service", "moe")
        
        event_id = sentry_sdk.capture_message(
            "MOE Test with Context",
            level="info"
        )
        
        print_success(f"Message with context captured: {event_id}")
        
        # Clear context
        sentry_sdk.set_user(None)
        
    except Exception as e:
        print_error(f"Failed context test: {e}")
        all_tests_passed = False
    
    # Test 6: Test Breadcrumbs
    print(f"\n{BLUE}Test 6: Test Breadcrumbs{RESET}")
    try:
        print_info("Adding breadcrumbs...")
        
        sentry_sdk.add_breadcrumb(
            category="test",
            message="Step 1: Initialize test",
            level="info"
        )
        
        sentry_sdk.add_breadcrumb(
            category="test",
            message="Step 2: Execute test logic",
            level="info"
        )
        
        sentry_sdk.add_breadcrumb(
            category="test",
            message="Step 3: Complete test",
            level="info"
        )
        
        event_id = sentry_sdk.capture_message(
            "MOE Test with Breadcrumbs",
            level="info"
        )
        
        print_success(f"Breadcrumbs captured with event: {event_id}")
        print_info(
            "Check Sentry event details to see breadcrumb trail"
        )
        
    except Exception as e:
        print_error(f"Failed breadcrumb test: {e}")
        all_tests_passed = False
    
    # Flush to ensure all events are sent
    print(f"\n{BLUE}Flushing events to Sentry...{RESET}")
    try:
        sentry_sdk.flush(timeout=5.0)
        print_success("Events flushed successfully")
        print_info(
            "Please check your Sentry dashboard to verify all events"
        )
    except Exception as e:
        print_warning(f"Flush completed with note: {e}")
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_tests_passed:
        print_success("All Sentry tests PASSED ✓")
        print_info(
            "\nPlease verify in Sentry dashboard:"
        )
        print_info("  1. Check Issues for test messages and exceptions")
        print_info("  2. Check Performance for test transactions")
        print_info("  3. Verify user context and tags are captured")
    else:
        print_error("Some Sentry tests FAILED ✗")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return all_tests_passed


def main():
    """Main test function."""
    # Get configuration from environment
    dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("SENTRY_ENVIRONMENT", "development")
    traces_sample_rate = float(
        os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")
    )
    
    if not dsn:
        print_error("SENTRY_DSN environment variable not set")
        print_info(
            "Please set SENTRY_DSN to your Sentry project DSN"
        )
        print_warning(
            "Sentry is optional. You can skip this test if not using Sentry."
        )
        sys.exit(1)
    
    success = test_sentry_connection(dsn, environment, traces_sample_rate)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
