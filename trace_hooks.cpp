#include <dlfcn.h>
#include <cxxabi.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static thread_local int inside_hook = 0;

extern "C" __attribute__((no_instrument_function))
void __cyg_profile_func_enter(void* this_fn, void* call_site) {
    if (!this_fn) return;

    if (inside_hook) return;
    inside_hook = 1;

    Dl_info info;
    if (dladdr(this_fn, &info) && info.dli_sname) {
        int status = 0;
        char* demangled = abi::__cxa_demangle(info.dli_sname, nullptr, nullptr, &status);
        const char* func_name = (status == 0 && demangled) ? demangled : info.dli_sname;

        // 필터: 표준 라이브러리 제외, 사용자 네임스페이스 강제 통과
        if ((strncmp(func_name, "std::", 5) == 0 ||
             strncmp(func_name, "__gnu_cxx::", 11) == 0 ||
             strncmp(func_name, "__cxxabiv1::", 11) == 0) &&
            !(strstr(func_name, "Queue") || strstr(func_name, "PrimeTable") || strstr(func_name, "tests"))) {
            free(demangled);
            inside_hook = 0;
            return;
        }

        char buffer[512];
        int len = snprintf(buffer, sizeof(buffer), "[ENTER] %s (%p)\n", func_name, this_fn);
        write(1, buffer, len);

        free(demangled);
    }

    inside_hook = 0;
}

extern "C" __attribute__((no_instrument_function))
void __cyg_profile_func_exit(void* this_fn, void* call_site) {
    if (!this_fn) return;

    if (inside_hook) return;
    inside_hook = 1;

    Dl_info info;
    if (dladdr(this_fn, &info) && info.dli_sname) {
        int status = 0;
        char* demangled = abi::__cxa_demangle(info.dli_sname, nullptr, nullptr, &status);
        const char* func_name = (status == 0 && demangled) ? demangled : info.dli_sname;

        if ((strncmp(func_name, "std::", 5) == 0 ||
             strncmp(func_name, "__gnu_cxx::", 11) == 0 ||
             strncmp(func_name, "__cxxabiv1::", 11) == 0) &&
            !(strstr(func_name, "Queue") || strstr(func_name, "PrimeTable") || strstr(func_name, "tests"))) {
            free(demangled);
            inside_hook = 0;
            return;
        }

        char buffer[512];
        int len = snprintf(buffer, sizeof(buffer), "[EXIT] %s (%p)\n", func_name, this_fn);
        write(1, buffer, len);

        free(demangled);
    }

    inside_hook = 0;
}
