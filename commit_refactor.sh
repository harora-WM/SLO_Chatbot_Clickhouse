#!/bin/bash
cd /home/hardik121/kafka_put

# Add all changes
git add -A

# Create commit
git commit -m "Major refactoring: Clean directory structure with pipeline/ and chatbot/ separation

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
  CLAUDE.md          - Developer guide"

# Show status
echo "Commit created. Changes:"
git log --oneline -1
