import subprocess
import sys
import logging
import os

# Configure logging for this module
logger = logging.getLogger(__name__)

def run_pipeline(file_path):
    """
    Executes the main pipeline script (run_pipeline.py) with the provided file path.

    Args:
        file_path (str): The path to the Excel file to be processed by the pipeline.

    Returns:
        bool: True if the pipeline executed successfully, False otherwise.
    """
    pipeline_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'run_pipeline.py'))
    
    if not os.path.exists(pipeline_script_path):
        logger.error(f"Pipeline script not found at: {pipeline_script_path}")
        return False

    try:
        # Use sys.executable to ensure the same Python interpreter is used
        result = subprocess.run(
            [sys.executable, pipeline_script_path, file_path],
            capture_output=True,
            text=True,
            check=True  # Raise an exception for non-zero exit codes
        )
        logger.info(f"Pipeline executed successfully for {file_path}")
        logger.debug(f"Pipeline stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Pipeline stderr: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Pipeline execution failed for {file_path}. Exit Code: {e.returncode}")
        logger.error(f"Pipeline stdout: {e.stdout}")
        logger.error(f"Pipeline stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        logger.error(f"Python interpreter not found or pipeline script path is incorrect: {pipeline_script_path}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during pipeline execution: {e}")
        return False
