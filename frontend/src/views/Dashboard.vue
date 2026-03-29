<template>
  <div class="relative w-full min-h-screen bg-[#e3dfd5] font-sans text-[#222] p-6 md:p-12">
    
    <!-- Background Grid Lines -->
    <div class="absolute inset-0 pointer-events-none z-0">
        <div class="grid-line-v left-[25%] hidden md:block"></div>
        <div class="grid-line-v left-[50%]"></div>
        <div class="grid-line-v left-[75%] hidden md:block"></div>
        <div class="grid-line-h top-[15%]"></div>
    </div>

    <div class="relative z-10 max-w-5xl mx-auto bg-white border-2 border-[#b5b0a6] shadow-2xl flex flex-col overflow-hidden min-h-[70vh]">
      
      <!-- Header -->
      <header class="flex justify-between items-center border-b-2 border-[#b5b0a6] p-6 bg-[#e3dfd5]">
        <div>
          <h1 class="text-3xl font-medium tracking-tighter text-[#222]">Dashboard</h1>
          <p class="text-[9px] uppercase tracking-widest font-semibold text-gray-500 mt-2">
            Expense Management System
          </p>
        </div>
        <div class="flex gap-4 items-center">
          <span class="text-[10px] uppercase tracking-widest font-bold text-[#ef3f23] hidden md:block">
            {{ userName }}
          </span>
          <button @click="logout" class="text-[10px] uppercase tracking-widest font-bold text-gray-500 hover:text-[#ef3f23] transition-colors">
            LOGOUT
          </button>
        </div>
      </header>

      <!-- Main Content area -->
      <main class="flex-1 flex flex-col p-8 md:p-12 gap-8 bg-white">
        
        <div>
          <h2 class="text-4xl md:text-5xl font-medium tracking-tighter text-[#222] mb-2">Welcome back.</h2>
          <p class="text-sm font-medium text-gray-500">Here is your expense summary for this period.</p>
        </div>

        <div v-if="isLoading" class="flex-1 flex items-center justify-center p-12">
          <p class="text-[10px] uppercase tracking-widest font-bold text-[#ef3f23] animate-pulse">Loading Summary...</p>
        </div>

        <!-- Summary Cards -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
          
          <!-- Total Expenses Card -->
          <div 
            @click="$router.push('/my-expenses')" 
            class="border-2 border-[#b5b0a6] bg-[#f5f3f0] p-8 flex flex-col justify-between group hover:border-[#222] hover:bg-white transition-colors cursor-pointer"
          >
            <div>
              <p class="text-[10px] uppercase tracking-widest font-bold text-gray-500 mb-2 group-hover:text-[#222] transition-colors">
                My Total Expenses
              </p>
              <h3 class="text-6xl font-medium tracking-tighter text-[#222] group-hover:text-[#ef3f23] transition-colors">
                {{ totalExpensesCount }}
              </h3>
              <p class="text-sm font-bold text-gray-500 mt-2">
                Accumulated Amount: <span class="text-[#222]">{{ formatCurrency(totalExpensesAmount) }}</span>
              </p>
            </div>
            <div class="mt-8 flex justify-between items-center border-t-2 border-[#b5b0a6]/50 pt-6">
              <span class="text-[9px] uppercase tracking-widest font-bold text-[#222]">View Records &rarr;</span>
            </div>
          </div>

          <!-- Pending Approvals Card -->
          <div 
           
  v-if="role === 'manager' || role === 'admin'"
  @click="$router.push('/approvals')"
            class="border-2 border-[#b5b0a6] bg-[#f5f3f0] p-8 flex flex-col justify-between group hover:border-[#222] hover:bg-white transition-colors cursor-pointer relative overflow-hidden"
          >
            <div v-if="pendingApprovalsCount > 0" class="absolute top-0 right-0 w-16 h-16 bg-[#ef3f23]/10 rounded-bl-full flex items-start justify-end p-3">
               <span class="w-3 h-3 rounded-full bg-[#ef3f23] animate-pulse"></span>
            </div>

            <div>
              <p class="text-[10px] uppercase tracking-widest font-bold text-[#ef3f23] mb-2 flex items-center gap-2">
                Pending Approvals
              </p>
              <h3 class="text-6xl font-medium tracking-tighter text-[#222] group-hover:text-[#ef3f23] transition-colors">
                {{ pendingApprovalsCount }}
              </h3>
              <p class="text-sm font-bold text-gray-500 mt-2">Requires your review</p>
            </div>
            <div class="mt-8 flex justify-between items-center border-t-2 border-[#b5b0a6]/50 pt-6">
              <span class="text-[9px] uppercase tracking-widest font-bold text-[#222]">Manage Approvals &rarr;</span>
            </div>
          </div>

        </div>

        <!-- Quick Actions -->
        <div class="mt-auto pt-8 border-t-2 border-[#b5b0a6] flex flex-col sm:flex-row gap-4">
          <button @click="$router.push('/create-expense')" class="flex-1 bg-[#ef3f23] text-white py-5 text-[11px] uppercase tracking-[0.2em] font-bold hover:bg-[#222] transition-colors shadow-lg">
            + Create New Expense
          </button>
        </div>

      </main>

      <!-- Footer -->
      <div class="border-t-2 border-[#b5b0a6] p-4 bg-[#e3dfd5] text-center md:text-right">
          <span class="text-[9px] uppercase tracking-widest font-bold text-gray-400">
            &copy; UMNG
          </span>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import {
  getMyExpenses,
  getPendingApprovals,
  logout as apiLogout
} from "../services/api";

const router = useRouter();

const userName = ref("Employee");
const role = ref(localStorage.getItem("role"));

const isLoading = ref(true);

const totalExpensesCount = ref(0);
const totalExpensesAmount = ref(0);
const pendingApprovalsCount = ref(0);

onMounted(async () => {
  userName.value = localStorage.getItem("username") || "Employee";
  await fetchDashboardSummary();
});

const fetchDashboardSummary = async () => {
  isLoading.value = true;

  try {
    // ✅ 1. My expenses
    const res = await getMyExpenses();
    const expenses = res.data;

    totalExpensesCount.value = expenses.length;
    totalExpensesAmount.value = expenses.reduce(
      (sum, e) => sum + parseFloat(e.amount || 0),
      0
    );

    // ✅ 2. Only fetch approvals if manager/admin
    if (role.value === "manager" || role.value === "admin") {
      const approvalsRes = await getPendingApprovals();
      pendingApprovalsCount.value = approvalsRes.data.length;
    } else {
      pendingApprovalsCount.value = 0;
    }

  } catch (err) {
    console.error("Dashboard error:", err);
  } finally {
    isLoading.value = false;
  }
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(amount || 0);
};

const logout = () => {
  apiLogout();
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
.font-sans { font-family: 'Inter', sans-serif; }

.grid-line-v { position: absolute; top: 0; bottom: 0; width: 1px; background-image: linear-gradient(to bottom, #b5b0a6 50%, transparent 50%); background-size: 1px 6px; }
.grid-line-h { position: absolute; left: 0; right: 0; height: 1px; background-image: linear-gradient(to right, #b5b0a6 50%, transparent 50%); background-size: 6px 1px; }

/* Custom scrollbar for Reimbursement System aesthetics */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #b5b0a6; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #ef3f23; }
</style>