<template>
  <div class="relative w-full min-h-screen bg-[#e3dfd5] font-sans text-[#222] p-6 md:p-12">
    
    <!-- Background Grid Lines -->
    <div class="absolute inset-0 pointer-events-none z-0">
        <div class="grid-line-v left-[25%] hidden md:block"></div>
        <div class="grid-line-v left-[50%]"></div>
        <div class="grid-line-v left-[75%] hidden md:block"></div>
        <div class="grid-line-h top-[15%]"></div>
    </div>

    <div class="relative z-10 max-w-5xl mx-auto bg-white border-2 border-[#b5b0a6] shadow-2xl flex flex-col overflow-hidden">
      
      <!-- Header -->
      <header class="flex justify-between items-center border-b-2 border-[#b5b0a6] p-6 bg-[#e3dfd5]">
        <div>
          <h1 class="text-3xl font-medium tracking-tighter text-[#222]">Submit Expense</h1>
          <p class="text-[9px] uppercase tracking-widest font-semibold text-[#ef3f23] mt-2 flex items-center gap-2">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="square" stroke-linejoin="miter" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
            EMPLOYEE: {{ employeeName || 'LOADING...' }}
          </p>
        </div>
        <div class="hidden md:block text-right">
          <p class="text-[10px] uppercase tracking-widest font-bold text-gray-500">Reimbursement System Finance</p>
        </div>
      </header>

      <main class="flex flex-col md:flex-row">
        
        <!-- LEFT COLUMN: Receipt Upload & OCR -->
        <div class="w-full md:w-1/2 border-r-2 border-[#b5b0a6] p-8 flex flex-col gap-6 bg-[#f5f3f0]">
          
          <div>
            <h2 class="text-lg font-medium tracking-tight mb-2">1. Upload Receipt</h2>
            <p class="text-[10px] uppercase tracking-widest text-gray-500 mb-4">Our AI will automatically extract the details.</p>
            
            <div class="border-2 border-dashed border-[#b5b0a6] hover:border-[#ef3f23] transition-colors p-8 text-center bg-white relative cursor-pointer group">
              <input type="file" @change="handleFileUpload" accept="image/*,application/pdf" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
              <div class="flex flex-col items-center gap-3">
                <svg class="w-8 h-8 text-[#222] group-hover:text-[#ef3f23] transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="square" stroke-linejoin="miter" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                <span class="text-[10px] uppercase tracking-widest font-bold text-[#222]">
                  {{ file ? file.name : 'CLICK TO UPLOAD RECEIPT' }}
                </span>
              </div>
            </div>
            
            <button 
              @click="scan" 
              :disabled="!file || isScanning"
              class="w-full mt-4 bg-[#222] text-white py-4 text-[10px] uppercase tracking-[0.2em] font-bold hover:bg-[#ef3f23] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
            >
              <svg v-if="isScanning" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              {{ isScanning ? 'SCANNING RECEIPT...' : 'RUN OCR SCAN' }}
            </button>
          </div>

          <!-- Messages -->
          <div v-if="scanMessage" class="p-4 border border-[#b5b0a6] text-[10px] uppercase tracking-widest font-bold text-center" :class="scanError ? 'bg-[#ef3f23]/10 text-[#ef3f23]' : 'bg-emerald-50 text-emerald-600'">
            {{ scanMessage }}
          </div>
        </div>

        <!-- RIGHT COLUMN: Expense Details & Conversion -->
        <div class="w-full md:w-1/2 p-8 flex flex-col gap-6">
          <h2 class="text-lg font-medium tracking-tight mb-2">2. Verify Details</h2>
          
          <div class="flex flex-col gap-5">
            <!-- Amount & Currency -->
            <div class="flex flex-col gap-2">
              <label class="text-[9px] uppercase tracking-widest font-bold text-gray-500">Amount & Currency</label>
              <div class="flex gap-2">
                <input v-model="expenseForm.amount" type="number" step="0.01" placeholder="0.00" class="flex-1 bg-transparent border-b-2 border-[#b5b0a6] py-2 text-[#222] font-medium text-lg focus:outline-none focus:border-[#ef3f23]" />
                <select v-model="selectedCurrency" class="bg-transparent border-b-2 border-[#b5b0a6] py-2 text-[#222] font-bold text-[10px] uppercase tracking-widest focus:outline-none focus:border-[#ef3f23] cursor-pointer">
                  <option v-for="cur in currencies" :key="cur" :value="cur">{{ cur }}</option>
                </select>
              </div>
            </div>

            <!-- Currency Conversion Tool -->
            <div class="bg-[#f5f3f0] border border-[#b5b0a6] p-4 flex flex-col gap-3">
              <label class="text-[9px] uppercase tracking-widest font-bold text-[#ef3f23]">Convert to Home Currency</label>
              <div class="flex gap-2 items-center">
                <span class="text-[10px] font-bold text-gray-500">TO:</span>
                <select v-model="targetCurrency" class="flex-1 bg-white border border-[#b5b0a6] p-2 text-[10px] font-bold uppercase tracking-widest focus:outline-none focus:border-[#ef3f23]">
                  <option v-for="cur in currencies" :key="cur" :value="cur">{{ cur }}</option>
                </select>
                <button @click="convert" :disabled="isConverting || !expenseForm.amount" class="bg-[#222] text-white px-4 py-2 text-[9px] uppercase tracking-widest font-bold hover:bg-[#ef3f23] transition-colors disabled:opacity-50">
                  {{ isConverting ? '...' : 'CONVERT' }}
                </button>
              </div>
            </div>

            <!-- Date -->
            <div class="flex flex-col gap-2">
              <label class="text-[9px] uppercase tracking-widest font-bold text-gray-500">Date of Expense</label>
              <input v-model="expenseForm.date" type="date" class="bg-transparent border-b-2 border-[#b5b0a6] py-2 text-[#222] font-medium focus:outline-none focus:border-[#ef3f23]" />
            </div>

            <!-- Category -->
            <div class="flex flex-col gap-2">
              <label class="text-[9px] uppercase tracking-widest font-bold text-gray-500">Category</label>
              <select v-model="expenseForm.category" class="bg-transparent border-b-2 border-[#b5b0a6] py-2 text-[#222] font-medium text-sm focus:outline-none focus:border-[#ef3f23] cursor-pointer">
                <option value="" disabled>Select a category</option>
                <option value="travel">Travel</option>
<option value="meals">Meals</option>
<option value="office">Office Supplies</option>
<option value="software">Software</option>
<option value="training">Training</option>
<option value="other">Other</option>
              </select>
            </div>

            <!-- Description -->
            <div class="flex flex-col gap-2">
              <label class="text-[9px] uppercase tracking-widest font-bold text-gray-500">Description</label>
              <textarea v-model="expenseForm.description" rows="2" placeholder="Brief description of the expense..." class="bg-transparent border-b-2 border-[#b5b0a6] py-2 text-[#222] font-medium text-sm focus:outline-none focus:border-[#ef3f23] resize-none"></textarea>
            </div>

          </div>

          <button 
            @click="submit" 
            :disabled="isSubmitting"
            class="w-full mt-auto bg-[#ef3f23] text-white py-5 text-[11px] uppercase tracking-[0.2em] font-bold hover:bg-[#222] transition-colors shadow-lg disabled:opacity-50"
          >
            {{ isSubmitting ? 'SUBMITTING...' : 'SUBMIT EXPENSE RECORD' }}
          </button>

        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import {
  scanReceipt,
  createExpense,
  getCurrencies,
  convertCurrency as convertApi
} from "../services/api";
import { useRouter } from "vue-router";

const router = useRouter();

// =======================
// STATE
// =======================
const employeeName = ref(localStorage.getItem("username") || "Employee");
const file = ref(null);

const isScanning = ref(false);
const scanMessage = ref("");
const scanError = ref(false);

const isConverting = ref(false);
const isSubmitting = ref(false);

const currencies = ref([]);
const selectedCurrency = ref("INR");

const expenseForm = ref({
  amount: "",
  category: "",
  description: "",
  date: "",
  receipt_scan_id: null
});

// =======================
// INIT
// =======================
onMounted(async () => {
  await loadCurrencies();
});

// =======================
// FETCH CURRENCIES
// =======================
const loadCurrencies = async () => {
  try {
    const res = await getCurrencies();
    currencies.value = res.data || [];
  } catch (err) {
    console.error("Currency load failed:", err);
  }
};

// =======================
// FILE UPLOAD
// =======================
const handleFileUpload = (e) => {
  file.value = e.target.files[0];
  scanMessage.value = "";
};

// =======================
// OCR SCAN
// =======================
const scan = async () => {
  if (!file.value) return;

  isScanning.value = true;
  scanError.value = false;
  scanMessage.value = "";

  try {
    const res = await scanReceipt(file.value);

    const data = res.data;

    // Autofill from backend
    expenseForm.value.amount = data.amount_inr || data.extracted_amount || "";
    expenseForm.value.description = data.extracted_description || "";
    expenseForm.value.date = data.extracted_date || "";
    expenseForm.value.receipt_scan_id = data.id;

    if (data.extracted_currency) {
      selectedCurrency.value = data.extracted_currency;
    }

    scanMessage.value = "OCR successful";

  } catch (err) {
    console.error(err);
    scanError.value = true;
    scanMessage.value = "OCR failed. Fill manually.";
  } finally {
    isScanning.value = false;
  }
};

// =======================
// CONVERT
// =======================
const convert = async () => {
  if (!expenseForm.value.amount) return;

  isConverting.value = true;

  try {
    const res = await convertApi({
      amount: parseFloat(expenseForm.value.amount),
      currency: selectedCurrency.value
    });

    expenseForm.value.amount = res.data.amount_inr;

  } catch (err) {
    console.error(err);
    alert("Conversion failed");
  } finally {
    isConverting.value = false;
  }
};

// =======================
// SUBMIT
// =======================
const submit = async () => {
  if (!expenseForm.value.amount || !expenseForm.value.category || !expenseForm.value.date) {
    alert("Fill all required fields");
    return;
  }

  isSubmitting.value = true;

  try {
    await createExpense({
      amount: parseFloat(expenseForm.value.amount),
      category: expenseForm.value.category,
      description: expenseForm.value.description,
      date: expenseForm.value.date,
      receipt_scan_id: expenseForm.value.receipt_scan_id
    });

    alert("Expense submitted");
    router.push("/dashboard");

  } catch (err) {
    console.error(err);
    alert("Submission failed");
  } finally {
    isSubmitting.value = false;
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