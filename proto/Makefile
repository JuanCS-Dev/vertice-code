# A2A Protocol - Protobuf Compilation
# ====================================
#
# Compiles .proto files to Python using grpcio-tools.
#
# Usage:
#   make proto       - Compile all proto files
#   make clean       - Remove generated files
#   make install     - Install dependencies
#   make verify      - Verify generated files
#
# Author: JuanCS Dev
# Date: 2025-12-30

.PHONY: proto clean install verify all

# Directories
PROTO_DIR := $(shell pwd)
ROOT_DIR := $(shell dirname $(PROTO_DIR))
OUT_DIR := $(ROOT_DIR)/core/protocols/proto

# Proto files
PROTO_FILES := common.proto message.proto task.proto agent_card.proto service.proto

# Tools
PROTOC := python -m grpc_tools.protoc
PROTO_PATH := -I$(PROTO_DIR) -I$(ROOT_DIR)

# Default target
all: install proto verify

# Install dependencies
install:
	@echo "Installing protobuf dependencies..."
	pip install grpcio grpcio-tools protobuf rfc8785 joserfc
	@echo "Dependencies installed."

# Compile proto files
proto: $(OUT_DIR)
	@echo "Compiling proto files..."
	$(PROTOC) $(PROTO_PATH) \
		--python_out=$(OUT_DIR) \
		--grpc_python_out=$(OUT_DIR) \
		--pyi_out=$(OUT_DIR) \
		$(addprefix $(PROTO_DIR)/,$(PROTO_FILES))
	@echo "Proto files compiled to $(OUT_DIR)"
	@# Fix imports in generated files
	@./fix_imports.sh $(OUT_DIR) || true

# Create output directory
$(OUT_DIR):
	@mkdir -p $(OUT_DIR)
	@touch $(OUT_DIR)/__init__.py

# Remove generated files
clean:
	@echo "Cleaning generated files..."
	@rm -rf $(OUT_DIR)/*.py $(OUT_DIR)/*.pyi
	@echo "Clean complete."

# Verify generated files
verify:
	@echo "Verifying generated files..."
	@python -c "from core.protocols.proto import common_pb2; print('common_pb2 OK')" 2>/dev/null || echo "common_pb2: NOT FOUND"
	@python -c "from core.protocols.proto import message_pb2; print('message_pb2 OK')" 2>/dev/null || echo "message_pb2: NOT FOUND"
	@python -c "from core.protocols.proto import task_pb2; print('task_pb2 OK')" 2>/dev/null || echo "task_pb2: NOT FOUND"
	@python -c "from core.protocols.proto import agent_card_pb2; print('agent_card_pb2 OK')" 2>/dev/null || echo "agent_card_pb2: NOT FOUND"
	@python -c "from core.protocols.proto import service_pb2; print('service_pb2 OK')" 2>/dev/null || echo "service_pb2: NOT FOUND"
	@echo "Verification complete."

# Help
help:
	@echo "A2A Protocol Protobuf Compilation"
	@echo ""
	@echo "Targets:"
	@echo "  make all      - Install deps, compile, and verify"
	@echo "  make proto    - Compile proto files"
	@echo "  make clean    - Remove generated files"
	@echo "  make install  - Install dependencies"
	@echo "  make verify   - Verify generated files"
	@echo ""
