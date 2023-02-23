"""Endpoints for Sites and related resources."""

from fastapi import APIRouter, status

from app.schemas.sites import Site, Survey

router = APIRouter(
    prefix="/sites",
    tags=["sites"],
    # dependencies=[Depends(db_dependency_here??)],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Site Resource Operations
#==========================================================================================
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_site(site: Site) -> Site:
    pass

@router.get("/")
async def get_sites() -> list[Site]:
    pass

@router.get("/{id}")
async def get_site(id: int) -> Site:
    pass

@router.get("/{id}/sub-sites")
async def get_sub_sites(id: int) -> Site:
    pass

@router.put("/{id}")
async def update_site(id: int, data: Site) -> Site:
    pass

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(id: int):
    pass

#==========================================================================================
# Survey Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/surveys", status_code=status.HTTP_201_CREATED)
async def create_survey(id: int, survey: Survey) -> Survey:
    pass

@router.get("/{id}/surveys")
async def get_surveys(id: int) -> list[Survey]:
    pass

@router.get("/{id}/surveys/{survey_id}")
async def get_survey(id: int, survey_id: int) -> Survey:
    pass

@router.put("/{id}/surveys/{survey_id}")
async def update_survey(id: int, survey_id: int, data: Survey) -> Survey:
    pass

@router.delete("/{id}/surveys/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey(id: int, survey_id: int):
    pass
