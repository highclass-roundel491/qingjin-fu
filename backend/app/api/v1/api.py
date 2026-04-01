from fastapi import APIRouter
from .endpoints import users, poems, challenges, learning, stats, works, feihualing, relay, social, achievements, graph, timed_challenge, comments, ai, poets

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(poems.router, prefix="/poems", tags=["poems"])
api_router.include_router(challenges.router, prefix="/challenges", tags=["challenges"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(works.router, prefix="/works", tags=["works"])
api_router.include_router(feihualing.router, prefix="/feihualing", tags=["feihualing"])
api_router.include_router(relay.router, prefix="/relay", tags=["relay"])
api_router.include_router(social.router, prefix="/social", tags=["social"])
api_router.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(timed_challenge.router, prefix="/timed-challenge", tags=["timed-challenge"])
api_router.include_router(comments.router, prefix="/works", tags=["comments"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(poets.router, prefix="/poets", tags=["poets"])
