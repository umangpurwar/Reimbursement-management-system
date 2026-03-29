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
          <h1 class="text-3xl font-medium tracking-tighter text-[#222]">Pending Approvals</h1>
          <p class="text-[9px] uppercase tracking-widest font-semibold text-gray-500 mt-2 flex items-center gap-2">
            Review & Manage Expense Requests
          </p>
        </div>
        <div class="flex gap-4 items-center">
          <button @click="$router.push('/dashboard')" class="text-[10px] uppercase tracking-widest font-bold text-gray-500 hover:text-[#ef3f23] transition-colors">
            Return &rarr;
          </button>
        </div>
      </header>

      <!-- Main Content area -->
      <main class="flex-1 flex flex-col bg-white">
        
        <!-- Table Header (Hidden on Mobile) -->
        <div class="hidden md:grid grid-cols-12 gap-4 border-b-2 border-[#b5b0a6] bg-[#f5f3f0] p-4 px-8 text-[9px] uppercase tracking-widest font-bold text-gray-500 items-center">
          <div class="col-span-3">Employee</div>
          <div class="col-span-3">Category</div>
          <div class="col-span-2 text-right">Amount</div>
          <div class="col-span-1 text-center">Status</div>
          <div class="col-span-3 text-right">Actions</div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="flex-1 flex items-center justify-center p-12">
          <p class="text-[10px] uppercase tracking-widest font-bold text-[#ef3f23] animate-pulse">Loading Pending Approvals...</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="approvals.length === 0" class="flex-1 flex flex-col items-center justify-center p-12 text-center border-b border-[#b5b0a6]">
          <svg class="w-12 h-12 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="square" stroke-linejoin="miter" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
          <h3 class="text-xl font-medium tracking-tight mb-2">All caught up!</h3>
          <p class="text-xs text-gray-500 mb-6">There are no pending expenses requiring your approval.</p>
        </div>

        <!-- Approvals List -->
        <div v-else class="flex flex-col flex-1 overflow-y-auto">
          <div 
            v-for="approval in approvals" 
            :key="approval.id" 
            class="grid grid-cols-1 md:grid-cols-12 gap-4 items-center border-b border-[#b5b0a6]/50 p-4 px-8 hover:bg-[#f5f3f0] transition-colors cursor-default group"
          >
            <!-- Employee -->
            <div class="col-span-1 md:col-span-3 flex flex-col">
              <span class="text-sm font-bold tracking-tight text-[#222]">{{ approval.user_detail?.username || 'Unknown' }}</span>
              <span class="md:hidden text-[9px] uppercase tracking-widest text-gray-500 mt-1">Employee</span>
            </div>
            
            <!-- Category -->
            <div class="col-span-1 md:col-span-3 flex flex-col">
              <span class="text-sm font-medium text-[#222]">{{ approval.category_display || 'Uncategorized' }}</span>
              <span class="text-[10px] text-gray-500 truncate max-w-[200px] mt-0.5">{{ approval.description || 'No description' }}</span>
            </div>

            <!-- Amount -->
            <div class="col-span-1 md:col-span-2 flex flex-col md:items-end mt-2 md:mt-0">
              <span class="md:hidden text-[9px] uppercase tracking-widest text-gray-500 mb-1">Amount</span>
              <span class="text-lg font-medium tracking-tighter text-[#222]">
                {{ formatCurrency(approval.amount, approval.currency) }}
              </span>
            </div>

            <!-- Status -->
            <div class="col-span-1 md:col-span-1 flex md:justify-center mt-2 md:mt-0">
              <span class="px-2 py-1 text-[8px] uppercase tracking-widest font-bold border bg-yellow-50 text-yellow-700 border-yellow-200">
                {{ approval.status_display || 'Pending' }}
              </span>
            </div>

            <!-- Actions -->
            <div class="col-span-1 md:col-span-3 flex gap-2 justify-start md:justify-end mt-4 md:mt-0">
              <button 
                @click="handleAction(approval.id, 'approve')"
                :disabled="isProcessing === approval.id"
                class="px-4 py-2 border-2 border-emerald-600 text-emerald-700 text-[9px] uppercase tracking-widest font-bold hover:bg-emerald-600 hover:text-white transition-colors disabled:opacity-50"
              >
                Approve
              </button>
              <button 
                @click="handleAction(approval.id, 'reject')"
                :disabled="isProcessing === approval.id"
                class="px-4 py-2 bg-[#222] text-white text-[9px] uppercase tracking-widest font-bold hover:bg-[#ef3f23] transition-colors disabled:opacity-50"
              >
                Reject
              </button>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="mt-auto border-t-2 border-[#b5b0a6] p-4 bg-[#e3dfd5] text-center md:text-left flex justify-between items-center">
            <span class="text-[9px] uppercase tracking-widest font-bold text-gray-500">
              PENDING REQUESTS: {{ approvals.length }}
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
import { ref, onMounted } from 'vue';
import api from '../services/api'; // Ensure this points to your configured Axios instance
import { useRouter } from 'vue-router';
const role = localStorage.getItem("role")

const router = useRouter();


// State
const employeeName = ref('');
const file = ref(null);
const isScanning = ref(false);
const scanMessage = ref('');
const scanError = ref(false);
const isConverting = ref(false);
const isSubmitting = ref(false);

const currencies = ref(['USD', 'EUR', 'GBP', 'INR', 'CAD', 'AUD', 'JPY']); // Fallback defaults
const selectedCurrency = ref('USD');
const targetCurrency = ref('USD');

const expenseForm = ref({
  amount: '',
  category: '',
  description: '',
  date: '',
  receipt_scan_id: null
});

// Initialization
onMounted(async () => {
  const role = localStorage.getItem("role")

  if (role !== "manager" && role !== "admin") {
    router.push("/dashboard")
    return
  }

  fetchApprovals()
})

// ================= API CALLS =================

const fetchEmployeeDetails = async () => {
  try {
    // Attempt to get user ID from local storage (set during login)
    const userId = localStorage.getItem('user_id');
    
    if (userId) {
      // Call endpoint by ID as requested
      const response = await api.get(`api/employees/${userId}/`);
      employeeName.value = response.data.name || response.data.full_name || response.data.username;
    } else {
      // Fallback if ID is not available but username is
      employeeName.value = localStorage.getItem('username') || 'Unknown Employee';
    }
  } catch (error) {
    console.error("Failed to fetch employee details", error);
    employeeName.value = localStorage.getItem('username') || 'Unknown Employee';
  }
};


const approvals = ref([])
const isLoading = ref(false)

const fetchApprovals = async () => {
  isLoading.value = true
  try {
    const res = await api.get("approvals/pending/")
    approvals.value = res.data
  } catch (err) {
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

const fetchCurrencies = async () => {
  try {
    const response = await api.get('receipts/currencies/');
    if (response.data && response.data.length > 0) {
      currencies.value = response.data;
    }
  } catch (error) {
    console.error("Failed to fetch currencies, using defaults.", error);
  }
};

// ================= ACTIONS =================

const handleFileUpload = (event) => {
  const selectedFile = event.target.files[0];
  if (selectedFile) {
    file.value = selectedFile;
    scanMessage.value = '';
  }
};

const scanReceipt = async () => {
  if (!file.value) return;
  
  isScanning.value = true;
  scanMessage.value = '';
  scanError.value = false;

  const formData = new FormData();
  formData.append('image', file.value);

  try {
    const response = await api.post('receipts/scan/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    // Autofill data from OCR response
    expenseForm.value.amount = response.data.amount || '';
    expenseForm.value.description = response.data.description || '';
    expenseForm.value.date = response.data.date || '';
    expenseForm.value.receipt_scan_id = response.data.id || response.data.receipt_scan_id || null;
    
    if (response.data.currency) {
      selectedCurrency.value = response.data.currency;
    }

    scanMessage.value = 'Receipt scanned successfully. Data extracted.';
  } catch (error) {
    console.error("OCR Scan failed:", error);
    scanError.value = true;
    scanMessage.value = 'OCR Scan failed. Please enter details manually.';
  } finally {
    isScanning.value = false;
  }
};

const convertCurrency = async () => {
  if (!expenseForm.value.amount) return;
  
  isConverting.value = true;
  try {
    const response = await api.post('receipts/convert/', {
      amount: parseFloat(expenseForm.value.amount),
      from_currency: selectedCurrency.value,
      to_currency: targetCurrency.value
    });

    // Update the amount and currency to the converted values
    expenseForm.value.amount = response.data.converted_amount || response.data.amount;
    selectedCurrency.value = targetCurrency.value;
    
  } catch (error) {
    console.error("Currency conversion failed:", error);
    alert("Currency conversion failed. Please try again.");
  } finally {
    isConverting.value = false;
  }
};

const submitExpense = async () => {
  if (!expenseForm.value.amount || !expenseForm.value.category || !expenseForm.value.date) {
    alert("Please fill in all required fields (Amount, Category, Date).");
    return;
  }

  isSubmitting.value = true;
  try {
    await api.post('expenses/', {
      amount: parseFloat(expenseForm.value.amount),
      currency: selectedCurrency.value,
      category: expenseForm.value.category,
      description: expenseForm.value.description,
      date: expenseForm.value.date,
      receipt_scan_id: expenseForm.value.receipt_scan_id
    });

    alert("Expense submitted successfully!");
    
    // Optional: Route back to dashboard or clear form
    router.push('/dashboard');
    
  } catch (error) {
    console.error("Expense submission failed:", error);
    alert("Failed to submit expense. Please check your data and try again.");
  } finally {
    isSubmitting.value = false;
  }
};

const isProcessing = ref(null)

const handleAction = async (id, action) => {
  isProcessing.value = id

  try {
    await api.patch(`approvals/${id}/action/`, {
      status: action === "approve" ? "approved" : "rejected"
    })

    // refresh list after action
    await fetchApprovals()

  } catch (err) {
    console.error(err)
    alert("Action failed")
  } finally {
    isProcessing.value = null
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
.font-sans { font-family: 'Inter', sans-serif; }

.grid-line-v { position: absolute; top: 0; bottom: 0; width: 1px; background-image: linear-gradient(to bottom, #b5b0a6 50%, transparent 50%); background-size: 1px 6px; }
.grid-line-h { position: absolute; left: 0; right: 0; height: 1px; background-image: linear-gradient(to right, #b5b0a6 50%, transparent 50%); background-size: 6px 1px; }

/* Hide number input spinners cleanly */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type="number"] {
  -moz-appearance: textfield;
}
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