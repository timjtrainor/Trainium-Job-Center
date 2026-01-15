import os
import time
from dotenv import load_dotenv
from langfuse import Langfuse

# Force debug logging for Langfuse
os.environ["LANGFUSE_DEBUG"] = "true"

load_dotenv()

def debug_connection():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    print(f"--- Debugging Langfuse Connection ---")
    print(f"Host: {host}")
    print(f"Public Key: {public_key[:8]}..." if public_key else "MISSING")
    print(f"Secret Key: {secret_key[:8]}..." if secret_key else "MISSING")
    
    lf = Langfuse()
    
    print("\n1. Pinging Auth Check...")
    if lf.auth_check():
        print("   ✅ Auth Check SUCCESS")
    else:
        print("   ❌ Auth Check FAILED")
        return

    print("\n2. Sending Test Trace (v3)...")
    # v3: Use context manager to start a trace/observation
    with lf.start_as_current_observation(name="debug-connection-test-v3") as trace:
        print("   Observation context active.")
        trace.update(metadata={"status": "testing"})
        # Child span
        with lf.start_as_current_observation(name="child-span") as span:
            span.end()
    
    print("   Trace created. Flushing...")
    start = time.time()
    lf.flush()
    end = time.time()
    print(f"   ✅ Flush Complete in {end - start:.2f}s")
    # v3 doesn't expose ID easily on the context wrapper without accessing .id property
    # But checking dashboard is enough.
    print(f"   Check dashboard for trace: 'debug-connection-test-v3'")

if __name__ == "__main__":
    debug_connection()
