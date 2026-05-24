from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.colorimetry.analyzer import analyze_subtono, decode_image

router = APIRouter(tags=["colorimetry"])


@router.post("/colorimetria")
async def colorimetria(image: UploadFile = File(...)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen")

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="La imagen está vacía")

    try:
        image_bgr = decode_image(contents)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        subtono = analyze_subtono(image_bgr)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"subtono": subtono}
