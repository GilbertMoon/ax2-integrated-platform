from django.urls import path

from attendance import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_board, name="board"),
    path("me/", views.my_attendance_view, name="my-attendance"),
    path("user/<int:user_id>/", views.user_attendance_view, name="user-attendance"),
    path("update/", views.update_attendance_view, name="update-attendance"),
    path("kiosk/", views.kiosk_page, name="kiosk"),                          # ← 이 줄 추가
    path("face-checkin/", views.face_checkin_view, name="face-checkin"),     # ← 이 줄 추가
]
