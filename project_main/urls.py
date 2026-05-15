from django.contrib import admin
from django.urls import path,include
from user import views as userviews
from django.contrib.auth import logout
from django.contrib.auth.views import LogoutView
from . import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls')),
    path('login/',userviews.Login,name='login'),
    path('register/',userviews.register,name='register'),
    path('logout/',LogoutView.as_view(template_name='index.html'),name='logout')
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
