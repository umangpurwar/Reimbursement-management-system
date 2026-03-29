import { createRouter, createWebHistory } from "vue-router";

// Views
import HomeView from "../views/HomeView.vue";
import LoginView from "../views/Login.vue";
import DashboardView from "../views/Dashboard.vue";
import CreateExpenseView from "../views/CreateExpense.vue";
import MyExpensesView from "../views/MyExpenses.vue";
import ApprovalsView from "../views/Approvals.vue";
import UnauthorizedView from "../views/UnauthorizedView.vue";

const routes = [
  { path: "/", component: HomeView },
  { path: "/login", component: LoginView },
  { path: "/unauthorized", component: UnauthorizedView },

  {
    path: "/dashboard",
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: "/create-expense",
    component: CreateExpenseView,
    meta: { requiresAuth: true },
  },
  {
    path: "/my-expenses",
    component: MyExpensesView,
    meta: { requiresAuth: true },
  },
  {
    path: "/approvals",
    component: ApprovalsView,
    meta: { requiresAuth: true, requiresManager: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 🔐 ROUTE GUARD
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("access_token");
  const role = localStorage.getItem("role");

  // 1. Public routes
  if (!to.meta.requiresAuth) {
    return next();
  }

  // 2. Not logged in
  if (!token) {
    return next("/login");
  }

  // 3. Role-based protection
  if (to.meta.requiresManager) {
    if (role !== "manager" && role !== "admin") {
      return next("/unauthorized");
    }
  }

  next();
});

export default router;