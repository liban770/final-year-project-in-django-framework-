from django.contrib import admin
from .models import Chapter, Feedback, Notification, Project, SupervisorAssignment

admin.site.register(Project)
admin.site.register(Chapter)
admin.site.register(Feedback)
admin.site.register(SupervisorAssignment)
admin.site.register(Notification)
