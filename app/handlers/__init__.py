from .errors import router as error_router
from .lang import router as lang_router
from .my_profile import router as profile_router
from .registration import router as registration_router
from .lookup import router as lookup_router

all_routers = [error_router, lang_router, profile_router, registration_router, lookup_router]
