from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),         # ✅ root handled by users app
    path('events/', include('events.urls')),
]

