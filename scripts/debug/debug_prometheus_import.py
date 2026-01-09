import os
import sys

# Simulation of the logic in vertice_cli/core/providers/prometheus_provider.py
# File path: /media/juan/DATA/Vertice-Code/vertice_cli/core/providers/prometheus_provider.py
file_path = os.path.join(os.getcwd(), "vertice_cli/core/providers/prometheus_provider.py")
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(file_path))))
print(f"File Path: {file_path}")
print(f"Calculated Root: {root_path}")

# Add to path
if root_path not in sys.path:
    sys.path.insert(0, root_path)

try:
    print("Attempting import...")
    from prometheus.main import PrometheusAgent
    from prometheus.core.orchestrator import PrometheusOrchestrator
    print("SUCCESS: Imported PrometheusAgent and PrometheusOrchestrator")
except ImportError as e:
    print(f"FAILED: {e}")
    # Try to see if prometheus exists in the calculated root
    prom_path = os.path.join(root_path, "prometheus")
    print(f"Checking for prometheus directory at: {prom_path}")
    if os.path.exists(prom_path):
        print(f"Prometheus directory EXISTS at {prom_path}")
        print(f"Contents: {os.listdir(prom_path)}")
    else:
        print(f"Prometheus directory DOES NOT EXIST at {prom_path}")
    
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"OTHER ERROR: {e}")
    traceback.print_exc()