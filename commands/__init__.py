# commands/__init__.py
from .start import router as start_router
from .homework import router as homework_router
from .files import router as files_router
from .admin import router as admin_router
from .storage import router as storage_router
from .ping import router as ping_router

all_routers = [
    start_router,
    homework_router,
    files_router,
    admin_router,
    storage_router,
    ping_router
]

__all__ = ['all_routers']