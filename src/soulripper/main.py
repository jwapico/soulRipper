import asyncio
import sys

from soulripper.utils import AppParams, extract_app_params, init_logger
from soulripper.cli import CLIOrchestrator

async def soulrip():
    config_filepath = __file__.replace("src/soulripper/main.py", "config.yaml")
    app_params: AppParams = extract_app_params(config_filepath)
    
    init_logger(app_params.log_filepath, app_params.log_level, app_params.db_echo)

    if len(sys.argv) > 1:
        cli_orchestrator = CLIOrchestrator(app_params)
        await cli_orchestrator.run()

def main():
    asyncio.run(soulrip())

if __name__ == "__main__":
    main()