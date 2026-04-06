import csv
from io import StringIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, ListView, TemplateView, UpdateView

from users.mixins import AdminRequiredMixin, StudentRequiredMixin, SupervisorRequiredMixin
from users.models import User

from .forms import ChapterForm, FeedbackForm, ProjectForm, SupervisorAssignmentForm, GroupMemberForm, ContactMessageForm
from .models import ActivityLog, Chapter, Feedback, Notification, Project, SupervisorAssignment, GroupMember, ContactMessage


class ProjectCreateUpdateView(StudentRequiredMixin, FormView):
    template_name = "projects/project_form.html"
    form_class = ProjectForm
    success_url = reverse_lazy("projects:student-project")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = Project.objects.filter(student=self.request.user).first()
        if project:
            context['group_members'] = project.group_members.all()
        else:
            context['group_members'] = []
        context['group_member_form'] = GroupMemberForm()
        context['project'] = project
        return context

    def get_form(self, form_class=None):
        form_class = form_class or self.get_form_class()
        kwargs = self.get_form_kwargs()
        project = Project.objects.filter(student=self.request.user).first()
        if project:
            kwargs['instance'] = project
        return form_class(**kwargs)

    def form_valid(self, form):
        project, created = Project.objects.get_or_create(
            student=self.request.user,
            defaults={
                "project_title": "",
                "description": "",
                "leader": self.request.user
            },
        )
        project.project_title = form.cleaned_data["project_title"]
        project.description = form.cleaned_data["description"]
        project.leader = form.cleaned_data["leader"]
        project.status = Project.Status.PENDING
        project.save(update_fields=["project_title", "description", "leader", "status"])

        # Handle group members from POST data
        member_names = self.request.POST.getlist('member_name[]')
        member_emails = self.request.POST.getlist('member_email[]')

        # Clear existing members and add new ones
        project.group_members.all().delete()  # Clear existing members

        for name, email in zip(member_names, member_emails):
            if name.strip():  # Only add if name is not empty
                GroupMember.objects.create(
                    project=project,
                    name=name.strip(),
                    email=email.strip() if email.strip() else ""
                )

        assignment = SupervisorAssignment.objects.filter(student=self.request.user).first()
        if assignment:
            Notification.objects.create(
                user=assignment.supervisor,
                message=f"{self.request.user.username} submitted project details.",
            )

        ActivityLog.objects.create(
            user=self.request.user,
            project=project,
            message=(
                f"{self.request.user.username} {'created' if created else 'updated'} project details for '{project.project_title}'."
            ),
        )

        messages.success(self.request, "Project details saved successfully.")
        return redirect(self.success_url)


class ChapterListView(StudentRequiredMixin, ListView):
    template_name = "projects/chapter_list.html"
    context_object_name = "chapters"

    def get_queryset(self):
        project = Project.objects.filter(student=self.request.user).first()
        if not project:
            return Chapter.objects.none()
        return Chapter.objects.filter(project=project).select_related("feedback").order_by("-submission_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.filter(student=self.request.user).first()
        return context


class ChapterCreateView(StudentRequiredMixin, CreateView):
    template_name = "projects/chapter_form.html"
    form_class = ChapterForm
    # Redirect back to the upload page so the form fields reset.
    success_url = reverse_lazy("projects:chapter-create")

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, student=request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.status = Chapter.Status.PENDING
        response = super().form_valid(form)

        assignment = SupervisorAssignment.objects.filter(student=self.request.user).first()
        if assignment:
            Notification.objects.create(
                user=assignment.supervisor,
                message=f"New chapter submitted: {form.instance.title} by {self.request.user.username}.",
            )

        ActivityLog.objects.create(
            user=self.request.user,
            project=self.project,
            message=f"{self.request.user.username} submitted chapter '{form.instance.title}'.",
        )

        messages.success(self.request, "Chapter submitted successfully.")
        return response


class ChapterUpdateView(StudentRequiredMixin, UpdateView):
    model = Chapter
    template_name = "projects/chapter_form.html"
    form_class = ChapterForm
    success_url = reverse_lazy("projects:student-chapters")

    def get_queryset(self):
        return Chapter.objects.filter(project__student=self.request.user)

    def form_valid(self, form):
        form.instance.status = Chapter.Status.PENDING
        response = super().form_valid(form)
        assignment = SupervisorAssignment.objects.filter(student=self.request.user).first()
        if assignment:
            Notification.objects.create(
                user=assignment.supervisor,
                message=f"Chapter updated: {form.instance.title} by {self.request.user.username}.",
            )

        ActivityLog.objects.create(
            user=self.request.user,
            project=form.instance.project,
            message=f"{self.request.user.username} updated chapter '{form.instance.title}'.",
        )

        messages.success(self.request, "Chapter updated successfully.")
        return response


class SupervisorStudentListView(SupervisorRequiredMixin, ListView):
    template_name = "projects/supervisor_students.html"
    context_object_name = "assignments"

    def get_queryset(self):
        return SupervisorAssignment.objects.filter(
            supervisor=self.request.user
        ).select_related("student").prefetch_related("student__project__group_members")


class SupervisorChapterReviewListView(SupervisorRequiredMixin, ListView):
    template_name = "projects/supervisor_chapters.html"
    context_object_name = "chapters"

    def get_queryset(self):
        student_ids = SupervisorAssignment.objects.filter(supervisor=self.request.user).values_list("student_id", flat=True)
        return (
            Chapter.objects.filter(project__student_id__in=student_ids)
            .select_related("project", "project__student", "feedback")
            .order_by("-submission_date")
        )


class FeedbackCreateUpdateView(SupervisorRequiredMixin, CreateView):
    template_name = "projects/feedback_form.html"
    form_class = FeedbackForm
    success_url = reverse_lazy("projects:supervisor-chapters")

    def dispatch(self, request, *args, **kwargs):
        self.chapter = get_object_or_404(Chapter, pk=kwargs["pk"])
        self.assignment = get_object_or_404(
            SupervisorAssignment,
            student=self.chapter.project.student,
            supervisor=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chapter"] = self.chapter
        return context

    def get_initial(self):
        initial = super().get_initial()
        feedback = Feedback.objects.filter(chapter=self.chapter).first()
        if feedback:
            initial["comment"] = feedback.comment
        return initial

    def form_valid(self, form):
        Feedback.objects.update_or_create(
            chapter=self.chapter,
            defaults={
                "supervisor": self.request.user,
                "comment": form.cleaned_data["comment"],
            },
        )
        status = self.request.POST.get("status", Chapter.Status.REVIEWED)
        if status not in {Chapter.Status.REVIEWED, Chapter.Status.APPROVED, Chapter.Status.REJECTED}:
            status = Chapter.Status.REVIEWED
        self.chapter.status = status
        self.chapter.save(update_fields=["status"])

        if status == Chapter.Status.APPROVED:
            message_text = f"Your chapter '{self.chapter.title}' has been approved."
        elif status == Chapter.Status.REJECTED:
            message_text = f"Your chapter '{self.chapter.title}' has been rejected."
        else:
            message_text = f"Your chapter '{self.chapter.title}' has been reviewed."

        Notification.objects.create(user=self.chapter.project.student, message=message_text)

        ActivityLog.objects.create(
            user=self.request.user,
            project=self.chapter.project,
            message=f"{self.request.user.username} reviewed chapter '{self.chapter.title}' ({status}).",
        )

        messages.success(self.request, "Feedback saved successfully.")
        return HttpResponseRedirect(reverse_lazy("projects:supervisor-chapters"))


class FeedbackListView(StudentRequiredMixin, ListView):
    template_name = "projects/feedback_list.html"
    context_object_name = "chapters"

    def get_queryset(self):
        project = get_object_or_404(Project, student=self.request.user)
        return Chapter.objects.filter(project=project).select_related("feedback").order_by("-submission_date")


class SupervisorAssignmentCreateView(AdminRequiredMixin, CreateView):
    template_name = "projects/assignment_form.html"
    form_class = SupervisorAssignmentForm
    success_url = reverse_lazy("users:dashboard")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["student"].queryset = User.objects.filter(role=User.Role.STUDENT)
        form.fields["supervisor"].queryset = User.objects.filter(role=User.Role.SUPERVISOR)
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        Notification.objects.create(
            user=form.instance.student,
            message=f"You have been assigned to supervisor {form.instance.supervisor.username}.",
        )
        messages.success(self.request, "Supervisor assigned successfully.")
        return response


class ProjectListView(AdminRequiredMixin, ListView):
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return Project.objects.select_related("student", "leader").prefetch_related("group_members").order_by("-updated_at")


class ProjectStatusUpdateView(AdminRequiredMixin, View):
    def post(self, request, pk, action, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        if action == "approve":
            project.status = Project.Status.APPROVED
            message_text = f"Your project '{project.project_title}' has been approved."
            success_message = "Project approved successfully."
        elif action == "reject":
            project.status = Project.Status.REJECTED
            message_text = f"Your project '{project.project_title}' has been rejected. Please revise and resubmit."
            success_message = "Project rejected successfully."
        else:
            messages.error(request, "Invalid project action.")
            return redirect("projects:project-list")

        project.save(update_fields=["status"])
        Notification.objects.create(user=project.student, message=message_text)
        ActivityLog.objects.create(
            user=request.user,
            project=project,
            message=f"{request.user.username} {action}d project '{project.project_title}'.",
        )
        messages.success(request, success_message)
        return redirect("projects:project-list")


class GlobalSearchView(LoginRequiredMixin, TemplateView):
    template_name = "projects/search_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip().upper()
        context["query"] = q
        context["status"] = status
        if not q:
            context["students"] = User.objects.none()
            context["supervisors"] = User.objects.none()
            context["projects"] = Project.objects.none()
            return context

        student_qs = User.objects.filter(role=User.Role.STUDENT).filter(
            Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
        supervisor_qs = User.objects.filter(role=User.Role.SUPERVISOR).filter(
            Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
        project_qs = Project.objects.filter(
            Q(project_title__icontains=q)
            | Q(student__username__icontains=q)
            | Q(student__first_name__icontains=q)
            | Q(student__last_name__icontains=q)
        ).select_related("student").order_by("-updated_at")

        if status in {Chapter.Status.PENDING, Chapter.Status.REVIEWED, Chapter.Status.APPROVED, Chapter.Status.REJECTED}:
            project_qs = project_qs.filter(chapters__status=status).distinct()

        context["students"] = student_qs
        context["supervisors"] = supervisor_qs
        context["projects"] = project_qs
        return context


class ProjectReportsView(TemplateView):
    template_name = "projects/reports.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("users:login")
        if request.user.role not in {User.Role.ADMIN, User.Role.SUPERVISOR}:
            messages.error(request, "You do not have access to project reports.")
            return redirect("users:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def _parse_date(self, value):
        # Expect YYYY-MM-DD; ignore invalid values.
        try:
            from datetime import datetime

            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        is_admin = user.role == User.Role.ADMIN
        selected_supervisor_id = self.request.GET.get("supervisor") if is_admin else str(user.id)
        supervisor_mode = self.request.GET.get("supervisor") or ("all" if is_admin else str(user.id))
        from_date = self._parse_date(self.request.GET.get("from_date", ""))
        to_date = self._parse_date(self.request.GET.get("to_date", ""))

        context["from_date"] = self.request.GET.get("from_date", "")
        context["to_date"] = self.request.GET.get("to_date", "")

        chapters_qs = Chapter.objects.select_related("project", "project__student", "feedback")
        students_scope_ids = None
        if is_admin and supervisor_mode and supervisor_mode != "all":
            students_scope_ids = SupervisorAssignment.objects.filter(supervisor_id=supervisor_mode).values_list(
                "student_id", flat=True
            )
            chapters_qs = chapters_qs.filter(project__student_id__in=students_scope_ids)
            context["selected_supervisor_id"] = int(supervisor_mode)
        else:
            # Supervisor gets their own students automatically.
            if not is_admin:
                students_scope_ids = SupervisorAssignment.objects.filter(supervisor=user).values_list(
                    "student_id", flat=True
                )
                chapters_qs = chapters_qs.filter(project__student_id__in=students_scope_ids)
                context["selected_supervisor_id"] = user.id
            else:
                context["selected_supervisor_id"] = None

        if from_date:
            chapters_qs = chapters_qs.filter(submission_date__date__gte=from_date)
        if to_date:
            chapters_qs = chapters_qs.filter(submission_date__date__lte=to_date)

        context["total_students"] = User.objects.filter(
            role=User.Role.STUDENT, id__in=chapters_qs.values("project__student_id")
        ).distinct().count()
        context["total_projects"] = Project.objects.filter(id__in=chapters_qs.values("project_id")).distinct().count()
        context["pending_count"] = chapters_qs.filter(status=Chapter.Status.PENDING).count()
        context["reviewed_count"] = chapters_qs.filter(status=Chapter.Status.REVIEWED).count()
        context["approved_count"] = chapters_qs.filter(status=Chapter.Status.APPROVED).count()

        # Supervisor performance section
        supervisor_list = User.objects.filter(role=User.Role.SUPERVISOR).order_by("username")
        context["supervisors"] = supervisor_list
        context["performance_rows"] = []

        def feedback_date_filter(qs):
            if from_date:
                qs = qs.filter(reviewed_at__date__gte=from_date)
            if to_date:
                qs = qs.filter(reviewed_at__date__lte=to_date)
            return qs

        if is_admin and supervisor_mode and supervisor_mode != "all":
            perf_supervisors = supervisor_list.filter(id=int(supervisor_mode))
        else:
            perf_supervisors = supervisor_list if is_admin else supervisor_list.filter(id=user.id)

        for sup in perf_supervisors:
            reviewed_students_count = feedback_date_filter(
                Feedback.objects.filter(supervisor=sup)
                .values("chapter__project__student_id")
                .distinct()
            ).count()
            # feedback_date_filter returns a QuerySet; distinct+values works, count works.
            context["performance_rows"].append(
                {
                    "supervisor": sup,
                    "students_reviewed": reviewed_students_count,
                }
            )

        return context


class ProjectReportsExportView(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in {User.Role.ADMIN, User.Role.SUPERVISOR}:
            return redirect("users:login")
        return super().dispatch(request, *args, **kwargs)

    def _parse_date(self, value):
        from datetime import datetime

        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    def get(self, request, *args, **kwargs):
        user = request.user
        is_admin = user.role == User.Role.ADMIN
        supervisor_mode = request.GET.get("supervisor") or ("all" if is_admin else str(user.id))
        from_date = self._parse_date(request.GET.get("from_date", ""))
        to_date = self._parse_date(request.GET.get("to_date", ""))

        chapters_qs = Chapter.objects.all()
        if not is_admin:
            students_scope_ids = SupervisorAssignment.objects.filter(supervisor=user).values_list("student_id", flat=True)
            chapters_qs = chapters_qs.filter(project__student_id__in=students_scope_ids)
        else:
            if supervisor_mode != "all":
                students_scope_ids = SupervisorAssignment.objects.filter(supervisor_id=supervisor_mode).values_list(
                    "student_id", flat=True
                )
                chapters_qs = chapters_qs.filter(project__student_id__in=students_scope_ids)

        if from_date:
            chapters_qs = chapters_qs.filter(submission_date__date__gte=from_date)
        if to_date:
            chapters_qs = chapters_qs.filter(submission_date__date__lte=to_date)

        total_students = User.objects.filter(
            role=User.Role.STUDENT, id__in=chapters_qs.values("project__student_id")
        ).distinct().count()
        total_projects = Project.objects.filter(id__in=chapters_qs.values("project_id")).distinct().count()
        pending_count = chapters_qs.filter(status=Chapter.Status.PENDING).count()
        reviewed_count = chapters_qs.filter(status=Chapter.Status.REVIEWED).count()
        approved_count = chapters_qs.filter(status=Chapter.Status.APPROVED).count()

        def feedback_date_filter(qs):
            if from_date:
                qs = qs.filter(reviewed_at__date__gte=from_date)
            if to_date:
                qs = qs.filter(reviewed_at__date__lte=to_date)
            return qs

        supervisors_qs = User.objects.filter(role=User.Role.SUPERVISOR).order_by("username")
        if is_admin and supervisor_mode != "all":
            supervisors_qs = supervisors_qs.filter(id=int(supervisor_mode))
        elif not is_admin:
            supervisors_qs = supervisors_qs.filter(id=user.id)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "supervisor_username",
                "students_reviewed",
                "total_students",
                "total_projects",
                "pending_count",
                "reviewed_count",
                "approved_count",
            ]
        )

        for sup in supervisors_qs:
            reviewed_students_count = feedback_date_filter(
                Feedback.objects.filter(supervisor=sup)
                .values("chapter__project__student_id")
                .distinct()
            ).count()
            writer.writerow(
                [
                    sup.username,
                    reviewed_students_count,
                    total_students,
                    total_projects,
                    pending_count,
                    reviewed_count,
                    approved_count,
                ]
            )

        filename = "project_report.csv"
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ProjectSimilarityAjaxView(LoginRequiredMixin, View):
    """
    Returns similar project title matches for the project submission page.
    """

    def get(self, request, *args, **kwargs):
        q = (request.GET.get("q") or "").strip()
        if not q:
            return JsonResponse({"similar_titles": []})

        keywords = [word for word in q.split() if len(word) >= 3]
        if not keywords:
            return JsonResponse({"similar_titles": []})

        query = Q()
        for term in keywords:
            query |= Q(project_title__icontains=term)

        similar_projects = (
            Project.objects.filter(query)
            .exclude(project_title__iexact=q)
            .order_by("project_title")[:5]
        )

        return JsonResponse(
            {
                "similar_titles": [p.project_title for p in similar_projects]
            }
        )


class SearchSuggestionsAjaxView(LoginRequiredMixin, View):
    """
    Returns lightweight search suggestions for the navbar (AJAX).
    """

    def get(self, request, *args, **kwargs):
        q = (request.GET.get("q") or "").strip()
        if not q:
            return JsonResponse({"students": [], "supervisors": [], "projects": []})

        students_qs = (
            User.objects.filter(role=User.Role.STUDENT)
            .filter(
                Q(username__icontains=q)
                | Q(email__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
            .order_by("username")[:6]
        )

        supervisors_qs = (
            User.objects.filter(role=User.Role.SUPERVISOR)
            .filter(
                Q(username__icontains=q)
                | Q(email__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
            .order_by("username")[:6]
        )

        projects_qs = Project.objects.filter(project_title__icontains=q).select_related("student").order_by("-updated_at")[:6]

        return JsonResponse(
            {
                "students": [
                    {
                        "id": s.id,
                        "username": s.username,
                        "email": s.email,
                        "name": s.get_full_name() or s.username,
                    }
                    for s in students_qs
                ],
                "supervisors": [
                    {
                        "id": sup.id,
                        "username": sup.username,
                        "email": sup.email,
                        "name": sup.get_full_name() or sup.username,
                    }
                    for sup in supervisors_qs
                ],
                "projects": [
                    {
                        "id": p.id,
                        "title": p.project_title,
                        "student": p.student.username,
                        "updated_at": p.updated_at.isoformat(),
                    }
                    for p in projects_qs
                ],
            }
        )
