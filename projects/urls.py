from django.urls import path

from .views import (
    AdminSupervisorAttendanceView,
    ChapterCreateView,
    ChapterListView,
    ChapterUpdateView,
    DefenseScheduleView,
    FeedbackCreateUpdateView,
    FeedbackListView,
    ProjectCreateUpdateView,
    GlobalSearchView,
    ProjectReportsExportView,
    ProjectReportsView,
    ProjectSimilarityAjaxView,
    SearchSuggestionsAjaxView,
    ProjectListView,
    SupervisorAssignmentCreateView,
    SupervisorChapterReviewListView,
    SupervisorStudentAttendanceView,
    SupervisorStudentListView,
    ProjectStatusUpdateView,
)

app_name = "projects"

urlpatterns = [
    path("my-project/", ProjectCreateUpdateView.as_view(), name="student-project"),
    path("my-chapters/", ChapterListView.as_view(), name="student-chapters"),
    path("chapter/upload/", ChapterCreateView.as_view(), name="chapter-create"),
    path("chapter/<int:pk>/update/", ChapterUpdateView.as_view(), name="chapter-update"),
    path("feedbacks/", FeedbackListView.as_view(), name="student-feedbacks"),
    path("my-project/check-similar/", ProjectSimilarityAjaxView.as_view(), name="project-similar-ajax"),
    path("search/", GlobalSearchView.as_view(), name="search"),
    path("search/ajax/", SearchSuggestionsAjaxView.as_view(), name="search-ajax"),
    path("supervisor/students/", SupervisorStudentListView.as_view(), name="supervisor-students"),
    path("supervisor/attendance/", SupervisorStudentAttendanceView.as_view(), name="supervisor-attendance"),
    path("supervisor/chapters/", SupervisorChapterReviewListView.as_view(), name="supervisor-chapters"),
    path("supervisor/chapter/<int:pk>/feedback/", FeedbackCreateUpdateView.as_view(), name="feedback-create"),
    path("admin/assign-supervisor/", SupervisorAssignmentCreateView.as_view(), name="assign-supervisor"),
    path("admin/attendance/", AdminSupervisorAttendanceView.as_view(), name="admin-attendance"),
    path("admin/project/<int:pk>/schedule-defense/", DefenseScheduleView.as_view(), name="schedule-defense"),
    path("admin/project/<int:pk>/<str:action>/", ProjectStatusUpdateView.as_view(), name="project-status-update"),
    path("admin/projects/", ProjectListView.as_view(), name="project-list"),
    path("reports/", ProjectReportsView.as_view(), name="reports"),
    path("reports/export/", ProjectReportsExportView.as_view(), name="reports-export"),
]
