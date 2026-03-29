<template>
  <div class="relative w-full h-screen overflow-hidden bg-[#0a0000] font-sans">
    <!-- Background Gradient -->
    <div class="fixed inset-0 z-0 bg-[#4a0b00] overflow-hidden">
        <div class="absolute top-[-10%] left-[0%] w-[80%] h-[80%] bg-[#ff2a00] rounded-full mix-blend-screen filter blur-[140px] opacity-70 animate-pulse"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-[70%] h-[70%] bg-[#ff6600] rounded-full mix-blend-screen filter blur-[150px] opacity-80"></div>
    </div>

    <!-- Main Container -->
    <transition name="reveal" appear>
      <div class="relative z-10 w-[92vw] max-w-[1600px] h-[90vh] mx-auto mt-[5vh] bg-[#e3dfd5] shadow-2xl flex flex-col overflow-hidden">
        
        <!-- Grid Lines -->
        <div class="absolute inset-0 pointer-events-none z-0">
            <div class="grid-line-v left-[25%]"></div>
            <div class="grid-line-v left-[50%]"></div>
            <div class="grid-line-v left-[75%] hidden lg:block"></div>
            <div class="grid-line-h top-[20%]"></div>
        </div>

        <!-- Header -->
        <header class="absolute top-0 left-0 w-full h-[20%] flex z-20">
            <div class="w-[25%] h-full flex items-center justify-center font-bold tracking-[0.2em] text-[13px] text-black">Reimbursement System</div>
            <div class="w-[75%] h-full flex items-center px-8 justify-end">
                <router-link to="/" class="text-[9px] uppercase tracking-widest font-semibold text-gray-700 hover:text-[#ef3f23] transition-colors pointer-events-auto">
                    RETURN HOME
                </router-link>
            </div>
        </header>

        <!-- Login Form Area -->
        <main class="absolute top-[20%] bottom-0 left-0 w-full flex z-10">
            <!-- Left Empty Column for Aesthetics -->
            <div class="hidden md:block w-[25%] h-full"></div>
            
            <!-- Form Column -->
            <div class="w-full md:w-[50%] lg:w-[25%] h-full flex flex-col justify-center px-12 md:px-16 lg:px-12 pointer-events-auto">
                <h1 class="text-[3rem] font-medium tracking-tighter leading-none text-[#222] mb-12">
                    Log In
                </h1>
                
                <div class="flex flex-col gap-8">
                    <div class="relative">
                        <input 
                            v-model="username" 
                            type="text" 
                            placeholder="USERNAME" 
                            class="w-full bg-transparent border-b-2 border-[#b5b0a6] py-3 text-[#222] font-medium tracking-widest text-[10px] uppercase placeholder-gray-500 focus:outline-none focus:border-[#ef3f23] transition-colors"
                        />
                    </div>
                    
                    <div class="relative">
                        <input 
                            v-model="password" 
                            type="password" 
                            placeholder="PASSWORD" 
                            class="w-full bg-transparent border-b-2 border-[#b5b0a6] py-3 text-[#222] font-medium tracking-widest text-[10px] uppercase placeholder-gray-500 focus:outline-none focus:border-[#ef3f23] transition-colors"
                        />
                    </div>

                    <button 
                        @click="login" 
                        class="mt-6 w-full bg-[#222] hover:bg-[#ef3f23] text-[#e3dfd5] py-4 text-[10px] uppercase tracking-[0.2em] font-bold transition-all duration-300"
                    >
                        Access Dashboard
                    </button>

                    <button 
                        @click="$router.push('/register')" 
                        class="mt-2 text-[9px] uppercase tracking-widest font-semibold text-gray-600 hover:text-[#ef3f23] transition-colors text-left"
                    >
                        New user? Register here
                    </button>
                </div>
            </div>
        </main>

        <!-- Copyright Signature (Bottom Right) -->
        <div class="absolute bottom-6 right-8 z-30 pointer-events-none text-[9px] uppercase tracking-[0.2em] font-bold text-gray-500">
            &copy; UMNG
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { login as loginApi } from "../services/api"   // ✅ use your api.js

const router = useRouter()
const username = ref("")
const password = ref("")
const loading = ref(false)

const login = async () => {
  if (!username.value || !password.value) {
    alert("Please enter username and password")
    return
  }

  loading.value = true

  try {
    // ✅ Use centralized API function
    const data = await loginApi({
      username: username.value,
      password: password.value
    })

    // ✅ Save username (optional)
    localStorage.setItem("username", username.value)

    // ❌ REMOVE admin logic (not available from JWT)
    // Instead always go to dashboard

    router.push("/dashboard")

  } catch (error) {
  console.log("FULL ERROR:", error);
  console.log("RESPONSE:", error?.response);
  console.log("DATA:", error?.response?.data);

  alert(JSON.stringify(error?.response?.data || "Server error"));
} finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.font-sans { font-family: 'Inter', sans-serif; }
.grid-line-v { position: absolute; top: 0; bottom: 0; width: 1px; background-image: linear-gradient(to bottom, #b5b0a6 50%, transparent 50%); background-size: 1px 6px; }
.grid-line-h { position: absolute; left: 0; right: 0; height: 1px; background-image: linear-gradient(to right, #b5b0a6 50%, transparent 50%); background-size: 6px 1px; }
.reveal-enter-active { transition: opacity 0.8s ease, transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); }
.reveal-enter-from { opacity: 0; transform: scale(0.98); }
</style>