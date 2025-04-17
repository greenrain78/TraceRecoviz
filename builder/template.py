MAIN_TEMPLATE = """

#include "aspect_common.ah"

aspect {{LOGGER_NAME}} {

{{ADVICE_BLOCKS}}

};

"""
SIGNATURE_FUNCTION = "% %({PATTERN})"
SIGNATURE_METHOD = "% %::%({PATTERN})"

ADVICE_CLASS = """
    // ===== {{CLASS_NAME}} =====
    advice construction("{{CLASS_NAME}}") : after() {
        std::ostringstream oss;
        oss << "[CTOR   ] {{CLASS_NAME}}::" << tjp->signature();
        AspectLogger::log(oss.str());
    }

    advice destruction("{{CLASS_NAME}}") : before() {
        std::ostringstream oss;
        oss << "[DTOR   ] {{CLASS_NAME}}::" << tjp->signature();
        AspectLogger::log(oss.str());
    }
"""

ADVICE_FUNCTION = """

// --- Trace for: ({{SIGNATURE}}) ---
advice call("{{SIGNATURE}}") : before() {
    AspectLogger::depth()++;
    std::ostringstream oss;
    oss << AspectLogger::indent() << "[CALL   ] depth=" << AspectLogger::depth() << " " << tjp->signature() << "(" << {{ARGS_LOG}} << ")";
    AspectLogger::log(oss.str());
}
advice call("{{SIGNATURE}}") : after() {
    std::ostringstream oss;
    oss << AspectLogger::indent() << "[RETURN ] depth=" << AspectLogger::depth() << " " << tjp->signature();
    if (tjp->result()) {
        oss << " => " << *tjp->result();
    } else {
        oss << " => void";
    }
    AspectLogger::log(oss.str());
    AspectLogger::depth()--;
}
"""