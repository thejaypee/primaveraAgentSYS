#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from primaverum.crew import Primaverum

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'Base Logic Reasoning',
        'current_year': str(datetime.now().year)
    }

    try:
        Primaverum().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "Base Logic Reasoning",
        'current_year': str(datetime.now().year)
    }
    try:
        Primaverum().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Primaverum().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "Base Logic Reasoning",
        "current_year": str(datetime.now().year)
    }

    try:
        Primaverum().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_gui():
    """
    Run the Streamlit GUI.
    """
    import subprocess
    import os
    
    gui_path = os.path.join(os.path.dirname(__file__), "gui.py")
    try:
        subprocess.run(["streamlit", "run", gui_path])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        raise Exception(f"An error occurred while running the GUI: {e}")
