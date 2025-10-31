from graphs.CreatePlannerGraph import create_planner_graph
from .main_graph import create_eval_quiz_graph

__any__ = [
    "create_eval_quiz_graph",
    "create_planner_graph"
    ]


# krag/__init__.py

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # For older Python versions
    from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("graphs")
except PackageNotFoundError:
    __version__ = "unknown"

