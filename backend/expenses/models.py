from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Expense(models.Model):
    """
    Represents an expense submission that travels through
    a configurable multi-level approval workflow.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    class Category(models.TextChoices):
        TRAVEL = "travel", _("Travel")
        MEALS = "meals", _("Meals & Entertainment")
        OFFICE = "office", _("Office Supplies")
        SOFTWARE = "software", _("Software & Subscriptions")
        TRAINING = "training", _("Training & Development")
        OTHER = "other", _("Other")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name=_("Submitted By"),
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Amount"),
    )
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True,
        verbose_name=_("Category"),
    )
    description = models.TextField(
        verbose_name=_("Description"),
    )
    date = models.DateField(
        verbose_name=_("Expense Date"),
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    current_step = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Current Approval Step"),
        help_text=_("Tracks which approval level is active in the workflow."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        db_index=True,
    )

    class Meta:
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")
        ordering = ["-created_at"]
        indexes = [
            # Composite index for the most common dashboard query:
            # show me all pending expenses for this user, newest first
            models.Index(fields=["user", "status", "-created_at"], name="expense_user_status_idx"),
            # Composite index for admin/manager approval queues
            models.Index(fields=["status", "current_step"], name="expense_status_step_idx"),
        ]

    def __str__(self) -> str:
        return (
            f"Expense #{self.pk} | {self.user} | "
            f"{self.get_category_display()} | {self.amount} | {self.get_status_display()}"
        )


    # Workflow helpers
    

    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.PENDING

    @property
    def is_closed(self) -> bool:
        """True when the expense has reached a terminal state."""
        return self.status in {self.Status.APPROVED, self.Status.REJECTED}

    def advance_step(self, total_steps: int) -> None:
        """
        Move the workflow to the next approval step.
        Marks the expense fully approved when all steps are complete.
        Call this after an approver approves their step.
        """
        if self.current_step >= total_steps:
            self.status = self.Status.APPROVED
        else:
            self.current_step += 1
        self.save(update_fields=["status", "current_step"])

    def reject(self) -> None:
        self.status = self.Status.REJECTED
        self.save(update_fields=["status"])


class ApprovalStep(models.Model):
    """
    Represents a single approver's action within an Expense workflow.

    Each expense can have N steps (step_number 1 to N). The active step
    is determined by Expense.current_step. Steps are processed
    sequentially; a rejection at any step terminates the workflow.
    """

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="approval_steps",
        verbose_name=_("Expense"),
        db_index=True,
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,  # PROTECT: never silently delete approval history
        related_name="approval_steps",
        verbose_name=_("Approver"),
        db_index=True,
    )
    step_number = models.PositiveSmallIntegerField(
        verbose_name=_("Step Number"),
        help_text=_("1 = first approver, 2 = second, etc."),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name=_("Status"),
    )
    comment = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Comment"),
        help_text=_("Optional note left by the approver."),
    )
    action_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Action Date"),
        help_text=_("Populated automatically when the approver acts."),
    )

    class Meta:
        verbose_name = _("Approval Step")
        verbose_name_plural = _("Approval Steps")
        ordering = ["expense", "step_number"]
        # Each (expense, step_number) pair must be unique
        # prevents duplicate steps being inserted for the same expense.
        unique_together = [("expense", "step_number")]
        indexes = [
            # Fast lookup: "find all pending steps assigned to this approver"
            models.Index(fields=["approver", "status"], name="appr_stat_idx"),
        ]

    def __str__(self) -> str:
        return (
            f"Step {self.step_number} | Expense #{self.expense_id} | "
            f"{self.approver} | {self.get_status_display()}"
        )

    # Workflow helpers
   
    def approve(self, comment: str = "") -> None:
        """
        Mark this step approved, record a timestamp, then advance the
        parent expense to the next step (or fully approve it).
        """
        from django.utils import timezone

        self.status = self.Status.APPROVED
        self.comment = comment
        self.action_date = timezone.now()
        self.save(update_fields=["status", "comment", "action_date"])

        total_steps = self.expense.approval_steps.count()
        self.expense.advance_step(total_steps)

    def reject(self, comment: str = "") -> None:
        """
        Mark this step rejected, record a timestamp, and short-circuit
        the parent expense immediately.
        """
        from django.utils import timezone

        self.status = self.Status.REJECTED
        self.comment = comment
        self.action_date = timezone.now()
        self.save(update_fields=["status", "comment", "action_date"])

        self.expense.reject()