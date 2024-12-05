"""alltime11 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from common_api.views import OtpView, FileUploadView, token_refresh, token_invalidate, \
    AdminDashboardView, AdminSliderView, RewardListCreateAPIView, RewardApplyAPIView, AdminUserUpdateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/otp', OtpView.as_view(), name='otp_view'),
    path('api/token-refresh', token_refresh, name='token_refresh'),
    path('api/logout', token_invalidate, name='token_invalidate'),
    path('api/file-upload', FileUploadView.as_view()),
    path('api/users/', include('users.urls')),
    path('api/cricket/', include('cricket.urls')),
    path('api/rewards/apply', RewardApplyAPIView.as_view()),
    path('api/admin/dashboard', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('api/admin/sliders', AdminSliderView.as_view(), name='admin_slider'),
    path('api/admin/sliders/<int:pk>', AdminSliderView.as_view(), name='admin_slider_update_delete'),
    path('api/admin/rewards/', RewardListCreateAPIView.as_view()),
    path('api/admin/users/<str:uid>', AdminUserUpdateView.as_view())
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
