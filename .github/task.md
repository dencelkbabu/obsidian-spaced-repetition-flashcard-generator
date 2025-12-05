# Enhancement Implementation Tasks

**Version:** 3.23.0 → 3.24.x  
**Approach:** One feature at a time, test, confirm, commit

---

## ✅ Items to Implement (No Trade-offs)

### Phase 1: Quick Wins

- [ ] **Enhancement 1: Batch Week Processing**
  - [ ] Update CLI argument parsing for week ranges
  - [ ] Add week range validation
  - [ ] Test with `COMM1001 1-3`
  - [ ] Test with `COMM1001 1,3,5`
  - [ ] Test with `COMM1001 ALL`
  - [ ] Run full test suite (125 tests)
  - [ ] **USER CONFIRMATION REQUIRED**
  - [ ] Commit: `feat: add batch week processing support`
  - [ ] Version bump: 3.23.0 → **3.24.0** (MINOR - new feature)

- [ ] **Enhancement 2: Progress Indicators**
  - [ ] Add current file name to progress display
  - [ ] Add current concept name to progress
  - [ ] Add real-time cache hit counter
  - [ ] Add real-time success/error counter
  - [ ] Test with COMM1001 W01
  - [ ] Run full test suite (125 tests)
  - [ ] **USER CONFIRMATION REQUIRED**
  - [ ] Commit: `feat: enhance progress indicators with detailed status`
  - [ ] Version bump: 3.24.0 → **3.24.1** (PATCH - UX improvement)

- [ ] **Enhancement 3: Concept Cache Progress**
  - [ ] Add progress bar for concept loading
  - [ ] Add count display after loading
  - [ ] Test with 1,093 concept files
  - [ ] Run full test suite (125 tests)
  - [ ] **USER CONFIRMATION REQUIRED**
  - [ ] Commit: `feat: add progress indicator for concept cache loading`
  - [ ] Version bump: 3.24.1 → **3.24.2** (PATCH - UX improvement)

### Phase 2: Performance Optimizations

- [ ] **Optimization 1: Smart Cache Invalidation**
  - [ ] Update cache key to include Bloom's level
  - [ ] Update cache key to include difficulty
  - [ ] Test cache with different presets
  - [ ] Verify different presets create different cache files
  - [ ] Run full test suite (125 tests)
  - [ ] **USER CONFIRMATION REQUIRED**
  - [ ] Commit: `perf: improve cache key to include bloom and difficulty`
  - [ ] Version bump: 3.24.2 → **3.24.3** (PATCH - performance)

- [ ] **Optimization 2: Parallel File Reading**
  - [ ] Implement ThreadPoolExecutor for file reading
  - [ ] Add error handling for parallel operations
  - [ ] Test with 10+ files
  - [ ] Measure speedup
  - [ ] Run full test suite (125 tests)
  - [ ] **USER CONFIRMATION REQUIRED**
  - [ ] Commit: `perf: parallelize file reading for faster processing`
  - [ ] Version bump: 3.24.3 → **3.24.4** (PATCH - performance)

### Phase 3: Quality Features

- [ ] **Feature 1: Quality Metrics Report**
  - [ ] Add MCQ format validation metrics
  - [ ] Add concept coverage metrics
  - [ ] Add performance metrics
  - [ ] Display report after generation
  - [ ] Test with COMM1001 W01
  - [ ] Run full test suite (125 tests)
  - [ ] **USER CONFIRMATION REQUIRED**
  - [ ] Commit: `feat: add quality metrics report after generation`
  - [ ] Version bump: 3.24.4 → **3.25.0** (MINOR - new feature)

- [ ] **Feature 2: Wikilink Post-Processing (Optional)**
  - [ ] Add concept footer generation
  - [ ] Add "📚 Concepts Covered" section
  - [ ] Test SR plugin compatibility
  - [ ] Test graph view integration
  - [ ] Test backlinks
  - [ ] Run full test suite (125 tests)
  - [ ] **USER CONFIRMATION REQUIRED**
  - [ ] Commit: `feat: add concept wikilinks footer for graph integration`
  - [ ] Version bump: 3.25.0 → **3.26.0** (MINOR - new feature)

---

## ❌ Items on Hold (Have Trade-offs)

- [x] ~~Increase Questions Per Prompt (2→5)~~ - Trade-off: Need quality testing
- [x] ~~Reduced LLM Context Size~~ - Trade-off: May reduce quality

---

## Testing Protocol for Each Enhancement

### Before Implementation:
1. Create feature branch (optional)
2. Review current code
3. Plan implementation

### During Implementation:
1. Write code
2. Add/update tests if needed
3. Run `pytest` (all 125 tests must pass)

### After Implementation:
1. Test new feature with COMM1001 W01 in dev mode
2. Verify output quality
3. Check for regressions
4. Document changes

### Before Commit:
1. Show user the changes
2. Demonstrate the feature working
3. Get explicit confirmation
4. Commit with conventional commit message
5. Update version number
6. Update CHANGELOG.md

---

## Current Status

- [/] **Phase 1: Quick Wins** (0/3 complete)
- [ ] **Phase 2: Performance** (0/2 complete)
- [ ] **Phase 3: Quality** (0/2 complete)

**Total Progress:** 0/7 enhancements complete

---

## Notes

- Each enhancement is independent
- Can skip any enhancement if not desired
- Can change order if needed
- All changes are backward compatible
- No breaking changes
