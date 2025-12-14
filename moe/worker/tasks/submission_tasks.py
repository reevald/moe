"""
Celery tasks for submission processing.

This module handles the end-to-end submission evaluation workflow.
"""

import json
import logging
import time
from typing import Any, Optional

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langfuse import Langfuse

from common.config import get_settings
from common.db import create_engine_from_url, create_session_factory
from modules import moe_service
from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def get_llm_client(settings):
    """Create and configure LLM client."""
    return ChatOpenAI(
        model_name=settings.math_model_name,
        openai_api_base=settings.openrouter_base_url,
        openai_api_key=settings.openrouter_api_key,
        temperature=0.0,
        request_timeout=120,  # 2 minutes timeout
        max_retries=2  # Retry up to 2 times on failure
    )


def get_langfuse_client(settings):
    """Create and configure Langfuse client."""
    return Langfuse(
        secret_key=settings.langfuse_secret_key,
        public_key=settings.langfuse_public_key,
        host=settings.langfuse_base_url
    )


@celery_app.task(name="worker.tasks.process_submission")
def process_submission(
    submission_id: str,
    problem_id: str,
    solution_latex: str
) -> dict[str, Any]:
    """
    Process submission through complete evaluation pipeline.

    Args:
        submission_id: Submission identifier
        problem_id: Problem identifier
        solution_latex: Solution in LaTeX format

    Returns:
        dict: Processing result

    Workflow:
        1. Guardrail check (25% progress)
        2. LaTeX to Lean conversion (50% progress)
        3. Lean validation (75% progress)
        4. Feedback generation (100% progress)
    """
    settings = get_settings()
    engine = create_engine_from_url(settings.db_url)
    session_factory = create_session_factory(engine)
    db = session_factory()

    try:
        logger.info(f"Processing submission {submission_id}")

        # Update status to processing
        moe_service.update_submission_status(
            db,
            submission_id,
            "processing",
            0
        )

        # Step 1: Guardrail check (Progress: 25%)
        logger.info(f"Step 1: Guardrail check for {submission_id}")
        is_valid_math, reason = guardrail_check(
            solution_latex,
            settings
        )

        if not is_valid_math:
            logger.warning(
                f"Guardrail rejected submission {submission_id}: "
                f"{reason}"
            )
            moe_service.update_submission_status(
                db,
                submission_id,
                "completed",
                100
            )
            moe_service.create_submission_result(
                db,
                submission_id,
                verdict="rejected",
                lean_is_valid=False,
                lean_status="guardrail_failed",
                lean_errors=[{"message": reason}],
                lean_remaining_goals=[],
                feedback=[
                    f"Submission rejected: {reason}. "
                    "Please provide a valid mathematical proof."
                ]
            )
            return {"status": "rejected", "reason": reason}

        moe_service.update_submission_status(
            db,
            submission_id,
            "processing",
            25
        )

        # Step 2: Convert LaTeX to Lean (Progress: 50%)
        logger.info(
            f"Step 2: Converting LaTeX to Lean for {submission_id}"
        )

        problem_data = moe_service.get_problem_by_id_from_supabase(
            problem_id,
            settings.supabase_url,
            settings.supabase_secret_key
        )

        if not problem_data:
            raise ValueError(f"Problem {problem_id} not found")

        lean_code = convert_latex_to_lean(
            solution_latex,
            problem_data,
            settings
        )

        moe_service.update_submission_status(
            db,
            submission_id,
            "processing",
            50
        )

        # Step 3: Validate with Lean LSP (Progress: 75%)
        logger.info(
            f"Step 3: Validating Lean code for {submission_id}"
        )
        validation_result = validate_with_lean_lsp(lean_code)

        moe_service.update_submission_status(
            db,
            submission_id,
            "processing",
            75
        )

        # Step 4: Generate feedback (Progress: 100%)
        logger.info(f"Step 4: Generating feedback for {submission_id}")
        feedback = generate_feedback(
            solution_latex,
            lean_code,
            validation_result,
            settings
        )

        # Determine verdict
        verdict = "accepted" if (
            validation_result["is_valid"]
        ) else "rejected"

        # Create result
        moe_service.create_submission_result(
            db,
            submission_id,
            verdict=verdict,
            lean_is_valid=validation_result["is_valid"],
            lean_status=validation_result["status"],
            lean_errors=validation_result.get("errors", []),
            lean_remaining_goals=validation_result.get(
                "remaining_goals",
                []
            ),
            feedback=feedback
        )

        # Update submission to completed
        moe_service.update_submission_status(
            db,
            submission_id,
            "completed",
            100
        )

        logger.info(
            f"Completed processing submission {submission_id}: "
            f"{verdict}"
        )
        return {"status": "success", "verdict": verdict}

    except Exception as e:
        logger.error(
            f"Error processing submission {submission_id}: {e}",
            exc_info=True
        )
        moe_service.update_submission_status(
            db,
            submission_id,
            "failed",
            0
        )
        raise
    finally:
        db.close()
        engine.dispose()


def guardrail_check(
    solution_latex: str,
    settings
) -> tuple[bool, Optional[str]]:
    """
    Check if submission is a valid mathematical solution.

    Args:
        solution_latex: Solution text
        settings: Application settings

    Returns:
        tuple: (is_valid, rejection_reason)
    """
    llm = get_llm_client(settings)
    langfuse = get_langfuse_client(settings)

    prompt_template = PromptTemplate(
        input_variables=["solution"],
        template="""
Analyze the following mathematical text and determine if it 
represents a genuine attempt at a mathematical proof or solution.

Return ONLY one of these responses:
- "VALID" if it is a mathematical proof/solution
- "INVALID: <reason>" if it is not

Text to analyze:
{solution}

Response:"""
    )

    trace = langfuse.trace(name="guardrail_check")
    prompt = prompt_template.format(solution=solution_latex)

    try:
        response = llm.invoke(prompt)
        result = response.content.strip()

        trace.generation(
            name="guardrail",
            input=prompt,
            output=result,
            model=settings.math_model_name
        )

        if result.startswith("VALID"):
            return True, None
        elif result.startswith("INVALID"):
            reason = result.replace("INVALID:", "").strip()
            return False, reason
        else:
            return False, "Unable to validate submission format"

    except Exception as e:
        logger.error(f"Guardrail check failed: {e}")
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            return False, "Validation timed out. Please try again."
        return False, "Internal validation error"


def convert_latex_to_lean(
    solution_latex: str,
    problem_data: dict[str, Any],
    settings
) -> str:
    """
    Convert LaTeX solution to Lean code.

    Args:
        solution_latex: Solution in LaTeX
        problem_data: Problem information
        settings: Application settings

    Returns:
        str: Lean code
    """
    llm = get_llm_client(settings)
    langfuse = get_langfuse_client(settings)

    prompt_template = PromptTemplate(
        input_variables=["problem", "solution"],
        template="""
Convert the following mathematical proof from LaTeX to Lean 4.

Problem Statement:
{problem}

Proof in LaTeX:
{solution}

Generate ONLY the Lean 4 code, no explanations:"""
    )

    trace = langfuse.trace(name="latex_to_lean")
    prompt = prompt_template.format(
        problem=problem_data.get("statement_latex", ""),
        solution=solution_latex
    )

    try:
        response = llm.invoke(prompt)
        lean_code = response.content.strip()

        trace.generation(
            name="conversion",
            input=prompt,
            output=lean_code,
            model=settings.math_model_name
        )

        return lean_code

    except TimeoutError as e:
        logger.error(f"LaTeX to Lean conversion timed out: {e}")
        raise ValueError(
            "LLM conversion timed out. The proof may be too complex. "
            "Please try simplifying your solution."
        )
    except Exception as e:
        logger.error(f"LaTeX to Lean conversion failed: {e}")
        # Check if it's a timeout-related error
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            raise ValueError(
                "LLM conversion timed out. The proof may be too complex. "
                "Please try simplifying your solution."
            )
        raise


def validate_with_lean_lsp(lean_code: str) -> dict[str, Any]:
    """
    Validate Lean code using Lean LSP MCP.

    Args:
        lean_code: Lean code to validate

    Returns:
        dict: Validation result

    Note:
        This is a placeholder. Actual implementation requires
        integration with Lean LSP MCP server.
    """
    # TODO: Implement actual Lean LSP MCP integration
    # For now, return a mock response
    logger.warning("Using mock Lean LSP validation")

    # Simulate validation
    time.sleep(1)

    # Mock success response
    return {
        "is_valid": True,
        "status": "success",
        "errors": [],
        "remaining_goals": []
    }


def generate_feedback(
    solution_latex: str,
    lean_code: str,
    validation_result: dict[str, Any],
    settings
) -> list[str]:
    """
    Generate human-readable feedback for submission.

    Args:
        solution_latex: Original LaTeX solution
        lean_code: Converted Lean code
        validation_result: Lean validation result
        settings: Application settings

    Returns:
        list: Feedback messages
    """
    llm = get_llm_client(settings)
    langfuse = get_langfuse_client(settings)

    validation_status = (
        "passed" if validation_result["is_valid"] else "failed"
    )

    prompt_template = PromptTemplate(
        input_variables=[
            "solution",
            "validation_status",
            "errors"
        ],
        template="""
Provide constructive feedback for this mathematical proof.

Proof:
{solution}

Lean Validation: {validation_status}
Errors: {errors}

Provide feedback in 2-3 clear sentences focusing on:
- Strengths of the proof
- Areas for improvement

Feedback:"""
    )

    trace = langfuse.trace(name="feedback_generation")
    prompt = prompt_template.format(
        solution=solution_latex,
        validation_status=validation_status,
        errors=json.dumps(validation_result.get("errors", []))
    )

    try:
        response = llm.invoke(prompt)
        feedback_text = response.content.strip()

        trace.generation(
            name="feedback",
            input=prompt,
            output=feedback_text,
            model=settings.math_model_name
        )

        return [feedback_text]

    except Exception as e:
        logger.error(f"Feedback generation failed: {e}")
        return [
            "Unable to generate detailed feedback at this time."
        ]
