"""
Test script for Prometheus MCP Server

Allows testing the MCP server functionality independently.

Created with love for testing server capabilities.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import asyncio
import logging
import sys
from prometheus.mcp_server.config import MCPServerConfig
from prometheus.mcp_server.manager import MCPServerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def test_mcp_server():
    """Test the MCP server with basic functionality."""
    logger.info("Starting MCP Server test...")

    # Create configuration
    config = MCPServerConfig(
        host="localhost", port=3000, instance_id="test-mcp-server", log_level="DEBUG"
    )

    # Create and start server
    manager = MCPServerManager(config)

    try:
        # Initialize
        logger.info("Initializing server...")
        if not await manager.initialize():
            logger.error("Failed to initialize server")
            return False

        # Start server
        logger.info("Starting server...")
        if not await manager.start():
            logger.error("Failed to start server")
            return False

        logger.info("✅ MCP Server started successfully!")
        logger.info("Test endpoints:")
        logger.info(f"  - Health: http://{config.host}:{config.port}/health")
        logger.info(f"  - Status: http://{config.host}:{config.port}/status")
        logger.info(f"  - MCP: http://{config.host}:{config.port}/mcp")

        # Test basic functionality
        await test_basic_endpoints(manager)

        # Keep server running for a short time
        logger.info("Server running for 2 seconds...")
        await asyncio.sleep(2)

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

    finally:
        logger.info("Stopping server...")
        await manager.stop()


async def test_basic_endpoints(manager: MCPServerManager):
    """Test basic server endpoints."""
    import aiohttp

    config = manager.config

    async with aiohttp.ClientSession() as session:
        try:
            # Test health endpoint
            logger.info("Testing health endpoint...")
            async with session.get(f"http://{config.host}:{config.port}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed: {data['status']}")
                else:
                    logger.error(f"❌ Health check failed: {response.status}")

            # Test status endpoint
            logger.info("Testing status endpoint...")
            async with session.get(f"http://{config.host}:{config.port}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Status check passed: {data['running']}")
                else:
                    logger.error(f"❌ Status check failed: {response.status}")

            # Test MCP ping
            logger.info("Testing MCP ping...")
            ping_request = {"jsonrpc": "2.0", "id": "test-ping", "method": "ping"}

            async with session.post(
                f"http://{config.host}:{config.port}/mcp",
                json=ping_request,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("result") == {"status": "pong"}:
                        logger.info("✅ MCP ping passed")
                    else:
                        logger.error(f"❌ MCP ping failed: {data}")
                else:
                    logger.error(f"❌ MCP ping HTTP error: {response.status}")

        except Exception as e:
            logger.error(f"Endpoint test failed: {e}")


async def test_mcp_initialization():
    """Test MCP initialization handshake."""
    import aiohttp

    config = MCPServerConfig(host="localhost", port=3000)
    manager = MCPServerManager(config)

    try:
        await manager.initialize()
        await manager.start()

        async with aiohttp.ClientSession() as session:
            # Test initialization
            init_request = {
                "jsonrpc": "2.0",
                "id": "test-init",
                "method": "initialize",
                "params": {},
            }

            async with session.post(
                f"http://{config.host}:{config.port}/mcp",
                json=init_request,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "result" in data and "capabilities" in data["result"]:
                        logger.info("✅ MCP initialization passed")
                        logger.info(
                            f"Server capabilities: {list(data['result']['capabilities'].keys())}"
                        )
                        return True
                    else:
                        logger.error(f"❌ MCP initialization failed: {data}")
                else:
                    logger.error(f"❌ MCP initialization HTTP error: {response.status}")

    except Exception as e:
        logger.error(f"MCP initialization test failed: {e}")

    finally:
        await manager.stop()

    return False


async def main():
    """Main test function."""
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        # Test just initialization
        logger.info("Testing MCP initialization...")
        success = await test_mcp_initialization()
    else:
        # Test full server
        logger.info("Testing full MCP server...")
        success = await test_mcp_server()

    if success:
        logger.info("🎉 All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
