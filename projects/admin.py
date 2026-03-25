from django.contrib import admin
from .models import Chapter, Feedback, GroupMember, Notification, Project, SupervisorAssignment, ContactMessage

admin.site.register(Project)
admin.site.register(Chapter)
admin.site.register(Feedback)
admin.site.register(SupervisorAssignment)
admin.site.register(Notification)
admin.site.register(GroupMember)
admin.site.register(ContactMessage)
