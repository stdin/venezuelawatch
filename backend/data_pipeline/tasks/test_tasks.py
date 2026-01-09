"""
Test tasks to verify Celery configuration.

These tasks can be used to test that Celery workers are running
and tasks can be executed successfully.
"""
from celery import shared_task


@shared_task
def hello_world():
    """
    Simple test task that returns 'Hello World'.

    Returns:
        str: "Hello World"

    Usage:
        from data_pipeline.tasks.test_tasks import hello_world
        result = hello_world.delay()
        print(result.get(timeout=10))  # Should print "Hello World"
    """
    return "Hello World"


@shared_task
def add(x, y):
    """
    Simple test task that adds two numbers.

    Args:
        x: First number
        y: Second number

    Returns:
        Sum of x and y

    Usage:
        from data_pipeline.tasks.test_tasks import add
        result = add.delay(4, 6)
        print(result.get(timeout=10))  # Should print 10
    """
    return x + y
