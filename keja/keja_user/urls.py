"""Url configs."""
from rest_framework.routers import SimpleRouter

from keja.keja_user.views import ContactViewSet, KejaUserViewSet

router = SimpleRouter()
router.register(r'users', viewset=KejaUserViewSet, basename='user')
router.register(r'contacts', viewset=ContactViewSet, basename='contact')
urlpatterns = router.urls
