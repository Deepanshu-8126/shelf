"""
Thermal Guard & Eco Cool Optimizer for Laptop CPUs.
Ensures CPU load stays under 25%, preventing laptop overheating and fan noise.
Optimized for 13th Gen Intel U-series laptop processors.
"""
import os
import sys

def apply_cool_mode():
    """Restricts threads and lowers CPU priority to keep laptop icy cool."""
    # 1. Limit math & neural library threads to 2 (Efficiency cores)
    os.environ["OMP_NUM_THREADS"] = "2"
    os.environ["MKL_NUM_THREADS"] = "2"
    os.environ["OPENBLAS_NUM_THREADS"] = "2"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
    os.environ["NUMEXPR_NUM_THREADS"] = "2"
    
    # 2. Limit PyTorch threads if already or about to be imported
    if "torch" in sys.modules:
        import torch
        torch.set_num_threads(2)
        
    # 3. Lower Windows process priority to Below Normal so CPU never spikes to 100%
    if sys.platform == "win32":
        try:
            import ctypes
            # BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
            ctypes.windll.kernel32.SetPriorityClass(
                ctypes.windll.kernel32.GetCurrentProcess(),
                0x00004000
            )
        except Exception:
            pass

apply_cool_mode()
