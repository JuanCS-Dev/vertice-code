#!/bin/bash
# Fix imports in generated proto files
# ====================================
#
# grpcio-tools generates absolute imports that need fixing
# for package-relative imports to work correctly.
#
# Author: JuanCS Dev
# Date: 2025-12-30

OUT_DIR="${1:-.}"

echo "Fixing imports in $OUT_DIR..."

# Fix imports in all generated Python files
for file in "$OUT_DIR"/*_pb2*.py; do
    if [ -f "$file" ]; then
        # Fix absolute imports to relative within proto package
        sed -i 's/^import common_pb2/from . import common_pb2/g' "$file"
        sed -i 's/^import message_pb2/from . import message_pb2/g' "$file"
        sed -i 's/^import task_pb2/from . import task_pb2/g' "$file"
        sed -i 's/^import agent_card_pb2/from . import agent_card_pb2/g' "$file"
        sed -i 's/^import service_pb2/from . import service_pb2/g' "$file"

        # Fix "from X import Y" style imports
        sed -i 's/^from common_pb2/from .common_pb2/g' "$file"
        sed -i 's/^from message_pb2/from .message_pb2/g' "$file"
        sed -i 's/^from task_pb2/from .task_pb2/g' "$file"
        sed -i 's/^from agent_card_pb2/from .agent_card_pb2/g' "$file"
        sed -i 's/^from service_pb2/from .service_pb2/g' "$file"

        echo "Fixed: $(basename "$file")"
    fi
done

echo "Import fixes complete."
