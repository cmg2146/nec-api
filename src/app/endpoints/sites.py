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

@router.get("/{site_id}")
async def get_site(site_id: int) -> Site:
    pass

@router.get("/{site_id}/sub-sites")
async def get_sub_sites(site_id: int) -> Site:
    pass

@router.put("/{site_id}")
async def update_site(site_id: int, data: Site) -> Site:
    pass

@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(site_id: int):
    pass

#==========================================================================================
# Survey Sub-Resource Operations
#==========================================================================================
@router.post("/{site_id}/surveys", status_code=status.HTTP_201_CREATED)
async def create_survey(site_id: int, survey: Survey) -> Survey:
    pass

@router.get("/{site_id}/surveys")
async def get_surveys(site_id: int) -> list[Survey]:
    pass

@router.get("/{site_id}/surveys/{survey_id}")
async def get_survey(site_id: int, survey_id: int) -> Survey:
    pass

@router.put("/{site_id}/surveys/{survey_id}")
async def update_survey(site_id: int, survey_id: int, data: Survey) -> Survey:
    pass

@router.delete("/{site_id}/surveys/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey(site_id: int, survey_id: int):
    pass
