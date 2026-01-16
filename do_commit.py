#!/usr/bin/env python3
import subprocess
import os

os.chdir('/home/hardik121/kafka_put')

# Git add
print("Adding all changes...")
subprocess.run(['git', 'add', '-A'], check=True)

# Git status
print("\nCurrent status:")
subprocess.run(['git', 'status', '--short'])

# Git commit
print("\nCreating commit...")
commit_message = """Major refactoring: Clean directory structure with pipeline/ and chatbot/ separation

BREAKING CHANGES:
- Moved all pipeline files to pipeline/ directory
- Moved SLO_Chatbot_Latest-v1/ to chatbot/ directory
- Created unified requirements.txt at root
- Created comprehensive README.md for users
- Updated CLAUDE.md for developers
- Organized documentation in docs/ folder
- Updated .gitignore for new structure

Benefits:
- Clear separation between data pipeline and chatbot
- Single venv for both projects (no duplication)
- Unified documentation at root level
- Cleaner, more professional structure
- Easier navigation and understanding

NO FUNCTIONAL CHANGES - all code works the same way

New structure:
  pipeline/          - Data ingestion (Kafka → ClickHouse)
  chatbot/           - AI monitoring (Claude Sonnet 4.5)
  docs/              - Shared documentation
  requirements.txt   - Unified dependencies
  README.md          - User guide
  CLAUDE.md          - Developer guide"""

subprocess.run(['git', 'commit', '-m', commit_message], check=True)

print("\n✅ Commit created successfully!")
subprocess.run(['git', 'log', '--oneline', '-1'])
