from django.contrib import admin
from django.urls import path, include

handler404 = 'core.views.page_not_found'

urlpatterns = [
    path('', include('posts.urls', namespace="posts")),
    path('about/', include('about.urls', namespace='about')),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
]
