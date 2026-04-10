from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


class SupervisorAssignment(models.Model):
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="supervisor_assignment",
        limit_choices_to={"role": "STUDENT"},
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_students",
        limit_choices_to={"role": "SUPERVISOR"},
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} -> {self.supervisor.username}"


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    group_member = models.ForeignKey(
        "GroupMember",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    taken_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "date"), ("group_member", "date")]
        ordering = ["-date"]

    def __str__(self):
        target = self.user.username if self.user else self.group_member.name if self.group_member else "Unknown"
        return f"{self.date} {target} - {self.status}"


class Project(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project",
        limit_choices_to={"role": "STUDENT"},
    )
    project_title = models.CharField(max_length=255, blank=True, default="", help_text="Title of the final year project")
    description = models.TextField(blank=True, default="", help_text="Detailed description of the project")
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="led_projects",
        limit_choices_to={"role": "STUDENT"},
        help_text="Project leader (can be different from the submitting student)"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    defense_date = models.DateTimeField(null=True, blank=True, help_text="Scheduled date and time for project defense")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project_title} (Leader: {self.leader.username})"


class GroupMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="group_members")
    name = models.CharField(max_length=255, help_text="Full name of the group member")
    email = models.EmailField(blank=True, help_text="Email address of the group member (optional)")

    class Meta:
        unique_together = ['project', 'name']

    def __str__(self):
        return f"{self.name} ({self.project.project_title})"


class Chapter(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWED = "REVIEWED", "Reviewed"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to="chapters/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])],
    )
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    def __str__(self):
        return f"{self.project.student.username} - {self.title}"


class Feedback(models.Model):
    chapter = models.OneToOneField(Chapter, on_delete=models.CASCADE, related_name="feedback")
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedbacks_given",
        limit_choices_to={"role": "SUPERVISOR"},
    )
    comment = models.TextField()
    annotated_file = models.FileField(
        upload_to="annotated_chapters/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])],
        blank=True,
        null=True,
        help_text="Upload the annotated version of the document with comments."
    )
    reviewed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback for {self.chapter.title}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"To {self.user.username}: {self.message}"


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
    )
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message


class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
