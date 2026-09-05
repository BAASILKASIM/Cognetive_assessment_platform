from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('instructions/', views.instructions, name='instructions'),
    path("participant/",views.participant,name="participant"),  
    path("lifestyle/", views.lifestyle,name="lifestyle"),
    path('reaction-test/', views.reaction_test, name='reaction_test'),
    path('save-reaction/',views.save_reaction,name='save_reaction'),
    path("debug/", views.session_debug, name="session_debug"),
    path("memory_test/", views.memory_test, name="memory_test"),
    path("save-visual-memory/",views.save_visual_memory,name="save_visual_memory",),  
    path("recognition-memory/",views.recognition_memory, name="recognition_memory",),  
    path("save-recognition-memory/",views.save_recognition_memory,name="save_recognition_memory",),  
    path("object-location-memory/",views.object_location_memory,name="object_location_memory",),  
    path("save-object-location/",views.save_object_location,name="save_object_location",),  
    path("delayed-recall/", views.delayed_recall, name="delayed_recall"),
    path("save-delayed-recall/", views.save_delayed_recall, name="save_delayed_recall"),
    path("clock-test/", views.clock_test, name="clock_test"),
    path("save-clock-test/", views.save_clock_test, name="save_clock_test"),
    path("report/", views.report, name="report"),
    path("retake/", views.retake_assessment, name="retake_assessment"),
]       