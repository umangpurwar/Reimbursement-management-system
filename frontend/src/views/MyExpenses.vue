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
          <h1 class="text-3xl font-medium tracking-tighter text-[#222]">My Expenses</h1>
          <p class="text-[9px] uppercase tracking-widest font-semibold text-gray-500 mt-2 flex items-center gap-2">
            Expense History & Status Tracking
          </p>
        </div>
        <div class="flex gap-4 items-center">
          <button @click="$router.push('/create-expense')" class="hidden md:block border-2 border-[#222] text-[#222] px-4 py-2 text-[9px] uppercase tracking-widest font-bold hover:bg-[#222] hover:text-white transition-colors">
            + New Expense
          </button>
          <button @click="$router.push('/dashboard')" class="text-[10px] uppercase tracking-widest font-bold text-gray-500 hover:text-[#ef3f23] transition-colors">
            Return &rarr;
          </button>
        </div>
      </header>

      <!-- Main Content area -->
      <main class="flex-1 flex flex-col bg-white">
        
        <!-- Table Header (Hidden on Mobile) -->
        <div class="hidden md:grid grid-cols-12 gap-4 border-b-2 border-[#b5b0a6] bg-[#f5f3f0] p-4 px-8 text-[9px] uppercase tracking-widest font-bold text-gray-500">
          <div class="col-span-3">Date</div>
          <div class="col-span-4">Category</div>
          <div class="col-span-2 text-right">Amount</div>
          <div class="col-span-3 text-right">Status</div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex-1 flex items-center justify-center p-12">
          <p class="text-[10px] uppercase tracking-widest font-bold text-[#ef3f23] animate-pulse">Loading Records...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="expenses.length === 0" class="flex-1 flex flex-col items-center justify-center p-12 text-center border-b border-[#b5b0a6]">
          <svg class="w-12 h-12 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="square" stroke-linejoin="miter" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
          <h3 class="text-xl font-medium tracking-tight mb-2">No expenses found</h3>
          <p class="text-xs text-gray-500 mb-6">You haven't submitted any expense records yet.</p>
          <button @click="$router.push('/create-expense')" class="bg-[#ef3f23] text-white px-8 py-3 text-[10px] uppercase tracking-[0.2em] font-bold hover:bg-[#222] transition-colors">
            Submit First Expense
          </button>
        </div>

        <!-- Expenses List -->
        <div v-else class="flex flex-col flex-1 overflow-y-auto">
          <div 
            v-for="expense in expenses" 
            :key="expense.id" 
            class="grid grid-cols-1 md:grid-cols-12 gap-4 items-center border-b border-[#b5b0a6]/50 p-4 px-8 hover:bg-[#f5f3f0] transition-colors cursor-default group"
          >
            <!-- Date -->
            <div class="col-span-1 md:col-span-3 flex flex-col">
              <span class="text-sm font-medium text-[#222]">{{ formatDate(expense.date) }}</span>
              <span class="md:hidden text-[9px] uppercase tracking-widest text-gray-500 mt-1">Date</span>
            </div>
            
            <!-- Category -->
            <div class="col-span-1 md:col-span-4 flex flex-col">
              <span class="text-sm font-bold tracking-tight text-[#222] group-hover:text-[#ef3f23] transition-colors">{{ expense.category_display }}</span>
              <span class="text-[10px] text-gray-500 truncate max-w-[200px] md:max-w-full mt-0.5">{{ expense.description || 'No description provided' }}</span>
            </div>

            <!-- Amount -->
            <div class="col-span-1 md:col-span-2 flex flex-col md:items-end mt-2 md:mt-0">
              <span class="md:hidden text-[9px] uppercase tracking-widest text-gray-500 mb-1">Amount</span>
              <span class="text-lg font-medium tracking-tighter text-[#222]">
                {{ formatCurrency(expense.amount, expense.currency) }}
              </span>
            </div>

            <!-- Status -->
            <div class="col-span-1 md:col-span-3 flex md:justify-end mt-2 md:mt-0">
              <span 
                class="px-3 py-1.5 text-[9px] uppercase tracking-widest font-bold border"
                :class="getStatusClasses(expense.status)"
              >
                {{ expense.status_display }}
              </span>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="mt-auto border-t-2 border-[#b5b0a6] p-4 bg-[#e3dfd5] text-center md:text-left flex justify-between items-center">
            <span class="text-[9px] uppercase tracking-widest font-bold text-gray-500">
              TOTAL RECORDS: {{ expenses.length }}
            </span>
            <span class="text-[9px] uppercase tracking-widest font-bold text-gray-400">
              &copy; UMNG
            </span>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { getMyExpenses } from "../services/api";

const expenses = ref([]);
const isLoading = ref(true);

onMounted(async () => {
  await fetchMyExpenses();
});

const fetchMyExpenses = async () => {
  isLoading.value = true;

  try {
    const res = await getMyExpenses();

    // handle both array and paginated response
    expenses.value = Array.isArray(res.data)
      ? res.data
      : res.data.results || [];

  } catch (error) {
    console.error("Failed to fetch expenses:", error);
    expenses.value = []; // ✅ NO FAKE DATA
  } finally {
    isLoading.value = false;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return "N/A";
  return new Date(dateString).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
  }).format(amount || 0);
};

const getStatusClasses = (status) => {
  const s = (status || "").toLowerCase();

  if (s === "approved") {
    return "bg-emerald-50 text-emerald-700 border-emerald-200";
  } else if (s === "rejected") {
    return "bg-red-50 text-red-700 border-red-200";
  } else {
    return "bg-yellow-50 text-yellow-700 border-yellow-200";
  }
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