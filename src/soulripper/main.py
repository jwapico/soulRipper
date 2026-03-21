import asyncio
import sys
import os

from soulripper.utils import AppParams, extract_app_params, init_logger
from soulripper.cli import CLIOrchestrator

async def main():
    app_params: AppParams = extract_app_params(f"{os.getcwd().replace('src', '')}/config.yaml")
    
    init_logger(app_params.log_filepath, app_params.log_level, app_params.db_echo)

    if len(sys.argv) > 1:
        cli_orchestrator = CLIOrchestrator(app_params)
        await cli_orchestrator.run()

if __name__ == "__main__":
    asyncio.run(main())