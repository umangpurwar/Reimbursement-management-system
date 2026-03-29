from django.urls import path

from .views import (
    ApprovalActionView,
    ExpenseCreateView,
    MyExpenseListView,
    PendingApprovalListView,
)

urlpatterns = [
    # Expense endpoints 
    # POST   /api/expenses/  -->  employee submits a new expense
    path("expenses/", ExpenseCreateView.as_view(), name="expense-create"),

    # GET    /api/expenses/my/    -->  employee views their own expenses : status= is pending or approved or rejected
    #        category is travel, meals, etc..
    path("expenses/my/", MyExpenseListView.as_view(), name="expense-my-list"),

    #  Approval endpoints
    # GET    /api/approvals/pending/ --> manager sees steps awaiting their action
    path("approvals/pending/", PendingApprovalListView.as_view(), name="approval-pending-list"),

    # PATCH  /api/approvals/<pk>/action/ --> approve or reject a step
    path("approvals/<int:pk>/action/", ApprovalActionView.as_view(), name="approval-action"),
]