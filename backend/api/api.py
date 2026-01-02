from ninja import NinjaAPI
import api.routers.auth as auth


# Create API instance
api = NinjaAPI(
    title='slotlist.online API',
    version='2.0.0',
    description='Backend API for slotlist.online - ArmA 3 mission planning and slotlist management',
    auth=auth.JWTAuth()
)

# Import routers after API is created to avoid circular imports
from api.routers import auth, mission, user, community, status, notification, mission_slot_template

# Register routers
api.add_router('/v1/auth/', auth.router, tags=['Authentication'], auth=None)
api.add_router('/v1/missions/', mission.router, tags=['Missions'])
api.add_router('/v1/missionSlotTemplates/', mission_slot_template.router, tags=['Mission Slot Templates'])
api.add_router('/v1/users/', user.router, tags=['Users'])
api.add_router('/v1/communities/', community.router, tags=['Communities'])
api.add_router('/v1/notifications/', notification.router, tags=['Notifications'])
api.add_router('/v1/', status.router, tags=['Status'])
