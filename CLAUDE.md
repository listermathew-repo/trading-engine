# Rules for Claude — MAF Backtest System

## Governance & Safety Rules

### Testing Requirements
1. **Always run tests after any change** to `strategy.py` or `engine.py`
   - Command: `python -m pytest -v` (when implemented)
   - No exceptions. If tests fail, do not proceed.
   - Report failure with full traceback and ask for guidance.

2. **Never delete or modify existing data files** (DuckDB)
   - `backtest_trading.duckdb.backup` is the source of truth
   - If data needs updating, create a migration script
   - Always keep a backup before any data operation

### Code Architecture Rules
3. **StrategyInterface contract is sacred**
   - Any change to `strategy.py` must maintain the Protocol contract:
     - `generate_signals(data) -> List[Dict]`
     - `calculate_indicators(data) -> Dict`
     - `filter_signals(signals, context) -> List[Dict]`
   - If changing signatures, update ALL implementations
   - Test that engine.py still accepts the strategy without errors

4. **Separation of concerns is non-negotiable**
   - `strategy.py`: Signal detection + risk calculation ONLY
   - `engine.py`: Execution simulation + metrics ONLY
   - `main.py`: Orchestration + testing ONLY
   - No cross-module dependencies except explicit strategy/engine interface

### Version Control Rules
5. **Atomic commits with clear messages**
   - One logical change per commit
   - Message format: `[PHASE] Description of change`
   - Example: `[Phase 2] Add liquidity sweep detection filter`
   - Every commit must pass tests before pushing

6. **Always pull latest state before major changes**
   - Check git status: `git status`
   - View recent commits: `git log --oneline -5`
   - Never force push without explicit user permission

### Documentation Rules
7. **Keep BACKTEST_ARCHITECTURE.md in sync**
   - Any file structure change → update file inventory section
   - Any function signature change → update module responsibilities
   - Any configuration change → update RULES.yaml

8. **Log significant decisions**
   - Add notes to FINDINGS.md or create new decision document
   - Include: what was tested, why it was chosen, expected impact
   - Example: "H4 Counter filter selected over Aligned because..."

### Failure Handling
9. **On any failure: STOP and ask**
   - Database connection error → stop, ask for guidance
   - Test failure → stop, report full output, ask for guidance
   - Unexpected behavior → stop, investigate, ask for confirmation
   - Never silently retry or skip failures

10. **Before autonomous changes**
    - Establish scope: "I will modify X, test with Y, verify Z"
    - Get user confirmation if scope > 1 file or affects multiple systems
    - Run tests after EACH file change, not just at the end

## Key Success Metrics

✅ Tests pass before every commit  
✅ StrategyInterface contract always valid  
✅ DuckDB never corrupted or deleted  
✅ Code remains readable and modular  
✅ Decisions are documented for future reference  

---

**Status**: Vault established. Ready for autonomous work under these rules.
