from fastapi import APIRouter


router_auth = APIRouter(prefix='/auth', tags=['Authorization management'])

router_analysis = APIRouter(prefix='/analysis', tags=['Analysis management'])
