# 🔥 PROMETHEUS FLIGHT TEST - Debugging During Flight
> **Mission**: Test Prometheus CLI/Shell em produção, debugando problemas conforme surgem
> **Date**: 2025-12-03
> **Status**: LIVE TESTING 🚀

---

## 📋 Pre-Flight Checklist

### Environment Setup
```bash
# 1. Confirm environment
cd /media/juan/DATA/projects/GEMINI-CLI-2/qwen-dev-cli
source venv/bin/activate  # if using venv

# 2. Check API Key
echo $GEMINI_API_KEY | head -c 20  # Should show key prefix

# 3. Quick health check
python -c "from vertice_cli.core.llm import llm_client; print('✅ LLM OK')"
```

### Launch Methods Available
```bash
# Method 1: Shell (Recommended for testing)
python -m vertice_cli.main shell --mode=main

# Method 2: TUI (Full UI)
python -m vertice_cli.main

# Method 3: Direct shell script
./qwen
```

---

## 🎯 TEST SUITE - Progressive Complexity

### 📊 Scoring System
```
✅ SUCCESS    - Task completed perfectly
⚠️  PARTIAL   - Task completed with issues
❌ FAIL       - Task failed completely
🐛 BUG FOUND  - Issue identified (document it!)
```

---

## LEVEL 1: FUNDAMENTALS (Warmup)
*Complexity: Trivial*
*Goal: Verify basic I/O and tool execution*

### Test 1.1: Hello World
**Task**: `Create a file called hello.py with a print statement`

**Expected**:
- ✅ File created in current directory
- ✅ Contains valid Python code
- ✅ No errors or warnings

**Log Results**:
```
Status: [ ]
Time: ___s
Issues: ________________________________
Notes: ________________________________
```

---

### Test 1.2: Read and Explain
**Task**: `Read hello.py and explain what it does`

**Expected**:
- ✅ File read successfully
- ✅ Clear explanation provided
- ✅ No hallucinations

**Log Results**:
```
Status: [ ]
Time: ___s
Issues: ________________________________
Notes: ________________________________
```

---

### Test 1.3: Simple Modification
**Task**: `Add a function to hello.py that returns the string 'Hello World' instead of printing`

**Expected**:
- ✅ File modified (not recreated)
- ✅ Function added correctly
- ✅ Original structure preserved

**Log Results**:
```
Status: [ ]
Time: ___s
Issues: ________________________________
Notes: ________________________________
```

---

## LEVEL 2: FILE OPERATIONS (Basic)
*Complexity: Easy*
*Goal: Test multi-file handling and directory operations*

### Test 2.1: Create Module Structure
**Task**: `Create a Python package called 'calculator' with __init__.py and operations.py. The operations.py should have add() and subtract() functions.`

**Expected**:
- ✅ Directory created
- ✅ Both files created
- ✅ Functions implemented with docstrings
- ✅ __init__.py properly imports functions

**Log Results**:
```
Status: [ ]
Time: ___s
Issues: ________________________________
Notes: ________________________________
```

---

### Test 2.2: Multi-File Coordination
**Task**: `Create a test_calculator.py that imports and tests the calculator package. Use assert statements.`

**Expected**:
- ✅ Imports work correctly
- ✅ At least 4 test cases
- ✅ Tests are runnable
- ✅ Tests pass when executed

**Validation**: `python test_calculator.py`

**Log Results**:
```
Status: [ ]
Time: ___s
Test Output: ________________________________
Issues: ________________________________
```

---

### Test 2.3: File Search and Modification
**Task**: `Find all .py files in the current directory and add a comment '# Tested on 2025-12-03' at the top of each`

**Expected**:
- ✅ All .py files found
- ✅ Comment added to each
- ✅ Existing code not broken

**Log Results**:
```
Status: [ ]
Files Modified: ___
Time: ___s
Issues: ________________________________
```

---

## LEVEL 3: DATA PROCESSING (Intermediate)
*Complexity: Medium*
*Goal: Test algorithmic thinking and data handling*

### Test 3.1: CSV Generator
**Task**: `Create a Python script that generates a CSV file with 100 rows of fake user data (name, email, age, city). Use only standard library.`

**Expected**:
- ✅ Script created
- ✅ CSV file generated
- ✅ Data looks realistic
- ✅ No external dependencies

**Validation**: `python generate_users.py && head -n 5 users.csv`

**Log Results**:
```
Status: [ ]
Time: ___s
Sample Output: ________________________________
Issues: ________________________________
```

---

### Test 3.2: Data Analysis Script
**Task**: `Create a script that reads users.csv and prints: average age, most common city, and age distribution histogram (ASCII art)`

**Expected**:
- ✅ Reads CSV correctly
- ✅ Statistics calculated
- ✅ Histogram renders properly
- ✅ No pandas required

**Log Results**:
```
Status: [ ]
Time: ___s
Output Quality: ________________________________
Issues: ________________________________
```

---

### Test 3.3: JSON to Markdown Converter
**Task**: `Create a script that converts a JSON file to a formatted Markdown table. Test it by creating sample.json with 5 products (name, price, stock) and converting it.`

**Expected**:
- ✅ JSON parsing works
- ✅ Markdown table formatted correctly
- ✅ Sample data created
- ✅ Conversion runs successfully

**Log Results**:
```
Status: [ ]
Time: ___s
Issues: ________________________________
```

---

## LEVEL 4: GIT OPERATIONS (Intermediate+)
*Complexity: Medium-High*
*Goal: Test Git integration and version control understanding*

### Test 4.1: Git Status Report
**Task**: `Show me the git status of this repository and list any uncommitted changes`

**Expected**:
- ✅ Git status displayed
- ✅ Uncommitted files listed
- ✅ Clear summary provided

**Log Results**:
```
Status: [ ]
Uncommitted Files: ___
Issues: ________________________________
```

---

### Test 4.2: Create Feature Branch Workflow
**Task**: `Create a new git branch called 'test/prometheus-demo', switch to it, and create a README_TEST.md with testing notes`

**Expected**:
- ✅ Branch created
- ✅ Switched to branch
- ✅ File created and committed
- ✅ Git log shows commit

**Validation**: `git branch && git log --oneline -n 1`

**Log Results**:
```
Status: [ ]
Time: ___s
Issues: ________________________________
```

---

### Test 4.3: Smart Diff Analysis
**Task**: `Show me the diff of the last 3 commits and summarize what changed in each`

**Expected**:
- ✅ Diffs retrieved
- ✅ Changes summarized clearly
- ✅ Key changes highlighted

**Log Results**:
```
Status: [ ]
Summary Quality: ________________________________
Issues: ________________________________
```

---

## LEVEL 5: ALGORITHMIC CHALLENGES (Hard)
*Complexity: Hard*
*Goal: Test problem-solving and code generation*

### Test 5.1: Prime Number Sieve
**Task**: `Implement the Sieve of Eratosthenes algorithm to find all prime numbers up to 10,000. Save to primes.py and print the first 20 primes.`

**Expected**:
- ✅ Algorithm correct
- ✅ Efficient implementation
- ✅ Script runnable
- ✅ Output matches known primes

**Validation**: `python primes.py`

**Log Results**:
```
Status: [ ]
Time: ___s
First 20 Primes: ________________________________
Algorithm Quality: ________________________________
Issues: ________________________________
```

---

### Test 5.2: Fibonacci with Memoization
**Task**: `Create a Python script with three implementations of Fibonacci: naive recursive, memoized recursive, and iterative. Include timing comparisons for n=35.`

**Expected**:
- ✅ All three implementations
- ✅ Timing code included
- ✅ Results accurate
- ✅ Performance differences shown

**Log Results**:
```
Status: [ ]
Time: ___s
Performance Delta: ________________________________
Issues: ________________________________
```

---

### Test 5.3: Binary Search Tree
**Task**: `Implement a Binary Search Tree class with insert, search, and in-order traversal methods. Include test cases.`

**Expected**:
- ✅ BST class implemented
- ✅ All methods working
- ✅ Tests included
- ✅ Edge cases handled

**Log Results**:
```
Status: [ ]
Time: ___s
Code Quality: ________________________________
Issues: ________________________________
```

---

## LEVEL 6: SYSTEM INTEGRATION (Very Hard)
*Complexity: Very Hard*
*Goal: Test complex multi-step workflows*

### Test 6.1: Project Scaffolder
**Task**: `Create a complete FastAPI project structure with: main.py (basic app), routers/users.py (CRUD endpoints), models/user.py (Pydantic model), tests/test_api.py (pytest tests). Include requirements.txt.`

**Expected**:
- ✅ All files created
- ✅ Proper imports
- ✅ FastAPI app runnable
- ✅ Tests pass

**Validation**: `pytest tests/test_api.py`

**Log Results**:
```
Status: [ ]
Time: ___s
Files Created: ___
Test Results: ________________________________
Issues: ________________________________
```

---

### Test 6.2: Automated Refactoring
**Task**: `Find all functions in the calculator/ package that are longer than 10 lines and refactor them to be more concise while maintaining functionality.`

**Expected**:
- ✅ Long functions identified
- ✅ Refactoring applied
- ✅ Tests still pass
- ✅ Code improved

**Log Results**:
```
Status: [ ]
Functions Refactored: ___
Issues: ________________________________
```

---

### Test 6.3: Documentation Generator
**Task**: `Scan all Python files created in this test session and generate a comprehensive docs/API.md file with function signatures, descriptions, and examples.`

**Expected**:
- ✅ All files scanned
- ✅ Documentation structured
- ✅ Examples included
- ✅ Markdown properly formatted

**Log Results**:
```
Status: [ ]
Time: ___s
Doc Quality: ________________________________
Issues: ________________________________
```

---

## LEVEL 7: META-PROGRAMMING (Expert)
*Complexity: Expert*
*Goal: Test self-awareness and advanced capabilities*

### Test 7.1: Code Review Yourself
**Task**: `Review the code you generated in Test 5.3 (BST) and provide a detailed critique with suggestions for improvement. Then implement your suggestions.`

**Expected**:
- ✅ Honest self-critique
- ✅ Valid suggestions
- ✅ Improvements applied
- ✅ Code quality enhanced

**Log Results**:
```
Status: [ ]
Time: ___s
Critique Quality: ________________________________
Improvements Made: ________________________________
```

---

### Test 7.2: Test Coverage Analysis
**Task**: `Analyze all test files created in this session and calculate approximate test coverage. Identify untested edge cases and create additional tests.`

**Expected**:
- ✅ Coverage estimated
- ✅ Gaps identified
- ✅ New tests created
- ✅ Coverage improved

**Log Results**:
```
Status: [ ]
Initial Coverage: ___%
Final Coverage: ___%
Issues: ________________________________
```

---

### Test 7.3: Generate This Test Suite
**Task**: `Create a new markdown file called CUSTOM_TEST.md that contains 5 new programming challenges similar to this test suite, but focused on a different domain (e.g., web scraping, CLI tools, etc.)`

**Expected**:
- ✅ New test suite created
- ✅ Progressive difficulty
- ✅ Clear expectations
- ✅ Runnable tasks

**Log Results**:
```
Status: [ ]
Time: ___s
Quality Assessment: ________________________________
```

---

## 🐛 BUG TRACKER

### Template for Each Bug Found
```markdown
#### BUG #___: [Short Description]
**Found During**: Test X.Y
**Severity**: 🔴 Critical / 🟡 Medium / 🟢 Low
**Symptoms**:
___

**Expected Behavior**:
___

**Actual Behavior**:
___

**Reproduction Steps**:
1. ___
2. ___

**Potential Cause**:
___

**Fix Applied** (if any):
___

**Status**: 🔴 Open / 🟡 In Progress / ✅ Fixed
```

---

## 📊 SUMMARY SCORECARD

### Overall Performance
```
Total Tests: 23
Passed: ___
Partial: ___
Failed: ___
Bugs Found: ___

Success Rate: ___%
Avg Response Time: ___s
```

### Capability Assessment
```
File Operations:      [ ] / 10
Code Generation:      [ ] / 10
Problem Solving:      [ ] / 10
Git Integration:      [ ] / 10
Multi-Step Planning:  [ ] / 10
Self-Awareness:       [ ] / 10
Error Recovery:       [ ] / 10

TOTAL SCORE: ___ / 70
```

### Key Insights
```
Strengths:
1. ___
2. ___
3. ___

Weaknesses:
1. ___
2. ___
3. ___

Priority Fixes:
1. ___
2. ___
3. ___
```

---

## 🚀 NEXT STEPS

After completing this test suite:

1. **Review Bug Tracker** - Prioritize critical issues
2. **Fix and Retest** - Apply fixes and rerun failed tests
3. **Document Patterns** - Note what works consistently
4. **Enhance Prompts** - Improve system prompts based on failures
5. **Add Tests to CI** - Convert passing tests to automated suite

---

## 📝 NOTES & OBSERVATIONS

*Use this space for freeform observations during testing*

```
Timestamp | Observation
----------|-------------
          |
          |
          |
          |
```

---

**Happy Flight Testing! 🛫**

*"The best way to find bugs is to use the system like you mean it."*
