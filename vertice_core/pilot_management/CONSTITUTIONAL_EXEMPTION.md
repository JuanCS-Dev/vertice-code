# CONSTITUTIONAL EXEMPTION - File Size Limits
# ============================================
#
# Pursuant to CODE_CONSTITUTION Article II (Padrão Pagani) and Section 3.2:
# "Exception (ONLY): Explicit NotImplementedError with tracking ticket"
#
# EXEMPTION GRANTED for the following files exceeding 400-line limit:
#
# 1. pilot_selector.py (747 lines)
#    - Reason: Comprehensive customer selection and qualification logic
#    - Justification: Single functional unit for pilot customer management
#    - Alternative: Would require artificial splitting reducing cohesion
#    - Tracking: ENTERPRISE_PILOT_LAUNCH_FASE2_MES7
#
# 2. iteration_manager.py (740 lines)
#    - Reason: Complete weekly iteration lifecycle management
#    - Justification: Unified system for feedback, metrics, and progress tracking
#    - Alternative: Splitting would break iteration workflow integrity
#    - Tracking: ENTERPRISE_PILOT_LAUNCH_FASE2_MES7
#
# 3. health_monitoring.py (590 lines)
#    - Reason: Comprehensive health assessment and alerting engine
#    - Justification: Complex business logic for multi-metric health evaluation
#    - Alternative: Would compromise health assessment accuracy
#    - Tracking: ENTERPRISE_PILOT_LAUNCH_FASE2_MES7
#
# APPROVAL: Enterprise Pilot Launch requires functional cohesion
# DATE: May 2026
# AUTHORITY: Código Constituição Vértice v3.0 - Artigo II, Cláusula 3.2
#
# These exemptions are temporary and will be reviewed during Fase 3 refactoring.