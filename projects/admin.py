from django.contrib import admin
from .models import Attendance, Chapter, Feedback, GroupMember, Notification, Project, SupervisorAssignment, ContactMessage


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['project_title', 'student', 'leader', 'status', 'defense_date', 'created_at']
    list_filter = ['status', 'defense_date', 'created_at']
    search_fields = ['project_title', 'student__username', 'leader__username']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Project Information', {
            'fields': ('student', 'project_title', 'description', 'leader', 'status')
        }),
        ('Defense Scheduling', {
            'fields': ('defense_date',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


admin.site.register(Chapter)
admin.site.register(Feedback)
admin.site.register(SupervisorAssignment)
admin.site.register(Attendance)
admin.site.register(Notification)
admin.site.register(GroupMember)
admin.site.register(ContactMessage)
