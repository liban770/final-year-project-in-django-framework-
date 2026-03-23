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


class Project(models.Model):
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project",
        limit_choices_to={"role": "STUDENT"},
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.student.username})"


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
