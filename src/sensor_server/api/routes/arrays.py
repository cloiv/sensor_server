"""Array upload and retrieval endpoints."""

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from sensor_server.core.processing import load_array_from_bytes, array_to_dict
from sensor_server.api.dependencies import get_storage

router = APIRouter(tags=["arrays"])


@router.post("/upload")
async def upload_numpy(file: UploadFile = File(...)) -> JSONResponse:
    """Receive a numpy .npy file from the client."""
    contents = await file.read()
    storage = get_storage()

    try:
        array = load_array_from_bytes(contents)
        index = storage.add(array)
        return JSONResponse({
            "status": "success",
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "index": index,
        })
    except ValueError as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400,
        )


@router.get("/arrays")
async def list_arrays() -> JSONResponse:
    """List all received numpy arrays with their metadata."""
    storage = get_storage()
    return JSONResponse({
        "count": storage.count(),
        "arrays": storage.list_all(),
    })


@router.get("/array/{index}")
async def get_array(index: int) -> JSONResponse:
    """Get a specific array by index (returns as nested list for JSON)."""
    storage = get_storage()
    array = storage.get(index)

    if array is None:
        return JSONResponse(
            {"status": "error", "message": "Array not found"},
            status_code=404,
        )

    return JSONResponse(array_to_dict(array))
