"""FastAPI routes for dataset ingestion, profiling, chat interaction, and session management."""

import logging
from typing import Any, Dict
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.agent.agent import AgentRunner
from app.config import settings
from app.schemas.agent import (
    ChatRequest,
    ChatResponse,
    MappingConfirmationRequest,
)
from app.schemas.dataset import DatasetPreview, DatasetProfile
from app.schemas.errors import ErrorResponse
from app.services.csv_service import CSVService
from app.services.profiling_service import ProfilingService
from app.services.session_service import session_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/datasets", tags=["Datasets & Analytics Agent"])


@router.post(
    "/upload",
    response_model=DatasetProfile,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid CSV file or empty dataset"},
        413: {"model": ErrorResponse, "description": "File exceeds maximum upload size"},
        422: {"model": ErrorResponse, "description": "Malformed CSV content"},
    },
)
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads an e-commerce sales CSV, validates it, and generates a full profile."""
    dataset_id, df, file_size = await CSVService.process_upload(file)

    # Create active session with isolated DataFrame
    session = session_service.create_session(
        dataset_id=dataset_id,
        filename=file.filename or "uploaded_data.csv",
        df=df,
        file_size_bytes=file_size,
    )

    # Profile dataset structure and detect semantic roles
    profile = ProfilingService.profile_dataset(
        dataset_id=dataset_id,
        filename=session.filename,
        file_size_bytes=file_size,
        df=df,
    )

    # Attach profile and seed confirmed mappings
    session_service.update_profile(dataset_id, profile)

    return profile


@router.get(
    "/{dataset_id}/profile",
    response_model=DatasetProfile,
    responses={404: {"model": ErrorResponse, "description": "Dataset session not found"}},
)
async def get_dataset_profile(dataset_id: str):
    """Retrieves computed structural profile and semantic mappings for a dataset."""
    session = session_service.get_session(dataset_id)
    if not session or not session.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset session '{dataset_id}' not found. Please upload a CSV first.",
        )
    return session.profile


@router.get(
    "/{dataset_id}/preview",
    response_model=DatasetPreview,
    responses={404: {"model": ErrorResponse, "description": "Dataset session not found"}},
)
async def get_dataset_preview(dataset_id: str, limit: int = 15):
    """Returns the top preview rows of the dataset for tabular display."""
    session = session_service.get_session(dataset_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset session '{dataset_id}' not found.",
        )

    preview_df = session.df.head(max(1, min(limit, 100)))
    records = []
    for r in preview_df.to_dict(orient="records"):
        # Ensure json-serializable null values
        clean_row = {
            k: (None if (v is None or (isinstance(v, float) and str(v) == "nan")) else v)
            for k, v in r.items()
        }
        records.append(clean_row)

    return DatasetPreview(
        dataset_id=dataset_id,
        filename=session.filename,
        total_rows=len(session.df),
        columns=list(session.df.columns),
        preview_rows=records,
    )


@router.post(
    "/{dataset_id}/mappings",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse, "description": "Dataset session not found"}},
)
async def update_mappings(dataset_id: str, payload: MappingConfirmationRequest):
    """Updates or confirms semantic column mappings for a dataset."""
    session = session_service.get_session(dataset_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset session '{dataset_id}' not found.",
        )

    # Validate that columns exist in DataFrame
    valid_cols = set(session.df.columns)
    for role, col in payload.mappings.items():
        if col not in valid_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{col}' does not exist in dataset. Available columns: {list(valid_cols)}",
            )

    session_service.update_mappings(dataset_id, payload.mappings)
    return {
        "status": "success",
        "dataset_id": dataset_id,
        "active_mappings": session.confirmed_mappings,
    }


@router.post(
    "/{dataset_id}/chat",
    response_model=ChatResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Dataset session not found"},
        422: {"model": ErrorResponse, "description": "Invalid query payload"},
    },
)
async def chat_with_dataset(dataset_id: str, request: ChatRequest):
    """Sends a natural language business question to the AI Data Analyst Agent."""
    session = session_service.get_session(dataset_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset session '{dataset_id}' not found. Please upload a dataset first.",
        )

    response = await AgentRunner.run(
        session=session,
        user_message=request.message,
        confirmed_mappings=request.confirmed_mappings,
    )
    return response


@router.delete(
    "/{dataset_id}",
    response_model=Dict[str, str],
    responses={404: {"model": ErrorResponse, "description": "Dataset session not found"}},
)
async def delete_dataset_session(dataset_id: str):
    """Terminates and cleans up an in-memory dataset session."""
    deleted = session_service.delete_session(dataset_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset session '{dataset_id}' not found.",
        )
    return {"status": "deleted", "dataset_id": dataset_id}
