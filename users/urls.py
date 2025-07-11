from django.urls import path
from . import views

urlpatterns = [
    # path('', views.landing_page, name='landing_page'),
    path('', views.test_home, name='test_home'),
    path('quote/', views.get_quote, name='get_quote'),
    path('enter/', views.enter_event_code, name='enter_event_code'),
    path('join/<str:event_code>/', views.enter_username, name='enter_username'),
    path('waiting/<str:event_code>/', views.waiting_room, name='waiting_room'),
    path('event/state/<str:event_code>/', views.event_state, name='event_state'),
    path('host/dashboard/', views.host_dashboard, name='host_dashboard'),
    path('host/start/<str:event_code>/', views.start_event, name='start_event'),
    path('leaderboard/<str:event_code>/', views.leaderboard, name='live_leaderboard'),
    path('leaderboard/state/<int:event_id>/', views.leaderboard_state, name='leaderboard_state'),
    path('calendar/', views.calendar_page, name='calendar_page'),
    path('calendar/data/', views.calendar_data, name='calendar_data'),
    path('booking/confirm/', views.confirm_booking, name='confirm_booking'),
    path('booking/summary/', views.booking_summary, name='booking_summary'),
    path('booking/<int:booking_id>/payment/', views.booking_payment, name='booking_payment'),
    path('pay/', views.pay_now, name='pay_now'),
    path('booking/<int:booking_id>/confirm/', views.booking_confirm, name='booking_confirm'),
    path('booking/<int:booking_id>/create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('contact/', views.contact_us, name='contact_us'),

]
