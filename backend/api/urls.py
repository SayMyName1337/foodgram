from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import TagViewSet, IngredientViewSet, UserViewSet


router_v1 = SimpleRouter()

router_v1.register(
    'tags',
    TagViewSet,
    basename='tags'
)

router_v1.register(
    'ingredients',
    IngredientViewSet,
    basename='ingredients'
)

router_v1.register(
    'users',
    UserViewSet,
    basename='users'
)

urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
]
