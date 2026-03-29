from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ApprovalStep, Expense
from .serializers import (
    ApprovalStepSerializer,
    ExpenseListSerializer,
    ExpenseSerializer,
)

User = get_user_model()

# Permissions

class IsEmployee(permissions.BasePermission):
    """Grants access only to users with role = employee."""
    message = "Only employees can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.EMPLOYEE
        )


class IsManagerOrAdmin(permissions.BasePermission):
    """Grants access only to managers or admins."""
    message = "Only managers or admins can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in {User.Role.MANAGER, User.Role.ADMIN}
        )


# 1. Create Expense  -->  POST /api/expenses/


class ExpenseCreateView(APIView):
    """
    Employee submits a new expense.

    Approval chain built automatically:
      - Step 1 : employee's direct manager (always required)
      - Step 2 : any admin user   (only when amount > 10 000)

    The entire operation is wrapped in a transaction so a partial
    failure (e.g. no manager found) rolls back both the Expense row
    and any ApprovalStep rows already written.
    """

    permission_classes = [IsEmployee]

    @transaction.atomic
    def post(self, request):
        serializer = ExpenseSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        #  Validate approval chain BEFORE writing anything 
        employee = request.user
        manager = employee.manager

        if manager is None:
            raise serializers.ValidationError(
                {
                    "non_field_errors": (
                        "You have no manager assigned. "
                        "Contact an administrator before submitting expenses."
                    )
                }
            )

        amount = serializer.validated_data["amount"]
        needs_admin_approval = amount > 10_000

        admin_approver = None
        if needs_admin_approval:
            admin_approver = (
                User.objects.filter(role=User.Role.ADMIN, is_active=True)
                .order_by("id")
                .first()
            )
            if admin_approver is None:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": (
                            "No active admin found to approve high-value expenses. "
                            "Contact your system administrator."
                        )
                    }
                )

        #  Persist expense 
        expense = serializer.save()  # user injected via HiddenField

        #  Build approval chain 
        steps = [
            ApprovalStep(
                expense=expense,
                approver=manager,
                step_number=1,
                status=ApprovalStep.Status.PENDING,
            )
        ]

        if needs_admin_approval:
            steps.append(
                ApprovalStep(
                    expense=expense,
                    approver=admin_approver,
                    step_number=2,
                    status=ApprovalStep.Status.PENDING,
                )
            )

        ApprovalStep.objects.bulk_create(steps)

        #  Return created expense 
        # Re-serialize with full approval_steps populated
        out = ExpenseSerializer(expense, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


# 2. Employee's expense history  :  GET /api/expenses/my/

class MyExpenseListView(generics.ListAPIView):
    """
    Returns all expenses submitted by the authenticated user,
    newest first. Uses the slim list serializer for efficient payloads.

    Query params (all optional):
      ?status=pending|approved|rejected   — filter by status
      ?category=travel|meals|...          — filter by category
    """

    serializer_class = ExpenseListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = (
            Expense.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("approval_steps__approver")
            .order_by("-created_at")
        )

        status_filter = self.request.query_params.get("status")
        if status_filter in Expense.Status.values:
            qs = qs.filter(status=status_filter)

        category_filter = self.request.query_params.get("category")
        if category_filter in Expense.Category.values:
            qs = qs.filter(category=category_filter)

        return qs


# 3. Manager approval queue  :  GET /api/approvals/pending/

class PendingApprovalListView(generics.ListAPIView):
    """
    Returns all ApprovalStep records where:
      - approver  = current user
      - status    = pending
      - step_number = expense.current_step   ← only the active step

    This ensures a manager only sees steps that are actually awaiting
    their action — not future steps that haven't been unlocked yet.
    """

    serializer_class = ApprovalStepSerializer
    permission_classes = [IsManagerOrAdmin]

    def get_queryset(self):
        return (
            ApprovalStep.objects.filter(
                approver=self.request.user,
                status=ApprovalStep.Status.PENDING,
                # Correlated filter: step_number must match the expense's live step
                step_number=models_F("expense__current_step"),
            )
            .select_related("approver", "expense__user")
            .prefetch_related("expense__approval_steps__approver")
            .order_by("expense__created_at")
        )


# 4. Approve / Reject a step  :  PATCH /api/approvals/<pk>/action/


class ApprovalActionView(APIView):
    """
    Approve or reject a single ApprovalStep.

    Payload:
        { "status": "approved" | "rejected", "comment": "optional text" }

    Rules enforced:
      1. Only the assigned approver can act on a step.
      2. The step must currently be pending.
      3. The step must be the active step on the expense (step_number == current_step).
      4. The parent expense must still be in a pending state.

    On approval:
      - step.status  : approved
      - step.action_date : now
      - If a next step exists : expense.current_step += 1
      - If no next step exists : expense.status = approved

    On rejection:
      - step.status    : rejected
      - step.action_date : now
      - expense.status  : rejected  (short-circuit; remaining steps stay pending)
    """

    permission_classes = [IsManagerOrAdmin]

    @transaction.atomic
    def patch(self, request, pk: int):
        step = get_object_or_404(
            ApprovalStep.objects.select_related("expense__user").select_for_update(),
            pk=pk,
        )

        #  Guard: only the assigned approver may act 
        if step.approver_id != request.user.id:
            return Response(
                {"detail": "You are not the assigned approver for this step."},
                status=status.HTTP_403_FORBIDDEN,
            )

        #  Guard: step must be pending 
        if step.status != ApprovalStep.Status.PENDING:
            return Response(
                {
                    "detail": (
                        f"This step has already been actioned "
                        f"({step.get_status_display()}) and cannot be changed."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guard: must be the active step on the expense 
        if step.step_number != step.expense.current_step:
            return Response(
                {
                    "detail": (
                        f"Step {step.step_number} is not the current active step "
                        f"(active: {step.expense.current_step})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        #  Guard: parent expense must be pending 
        if step.expense.status != Expense.Status.PENDING:
            return Response(
                {
                    "detail": (
                        f"The parent expense is already "
                        f"{step.expense.get_status_display()} and cannot be actioned."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate payload
        serializer = ApprovalStepSerializer(
            step,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        # Delegate to serializer.update() : model helpers (approve / reject)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)



# Import alias - avoids a name collision with the local `status` variable
from django.db.models import F as models_F  # noqa: E402 