# SoloNode Transaction Audit – Design Document

## 1. Introduction

### Purpose

The purpose of this Proof of Concept (POC) is to demonstrate **AI-assisted debugging and system stabilization** using a simulated transaction processing system. The system will intentionally contain defects that engineers must identify and resolve using **Claude AI assistance**.

### Concept

The POC follows a **Solo Hackathon-style debugging challenge** where an individual engineer receives a codebase with intentionally injected defects. The participant analyzes system behavior, collaborates with **Claude AI** to diagnose issues, and stabilizes the system.

### Key Goals

- Simulate a real-world debugging environment  
- Evaluate AI-assisted engineering workflows  
- Measure how effectively engineers collaborate with AI tools  
- Provide a structured environment for defect discovery and resolution

- ## 2. Implementation Strategy

The system will be developed in three stages.

---

### Stage 1 – Base System Development

A clean and correct transaction processing system will be implemented with modular architecture.

This base system will:

- Accept transaction inputs  
- Validate transaction structure  
- Verify API authentication  
- Calculate transaction fees  
- Log transaction activity  

The base version will serve as the reference implementation before defect injection.

---

### Stage 2 – Defect Injection

Once the base system is stable, controlled defects will be injected across different modules.

These defects will simulate common real-world software issues.

| Defect Category | Purpose |
|-----------------|---------|
| Silent Failure | Test debugging of hidden failures |
| State Mutation | Detect unintended data modification |
| Security Vulnerability | Identify insecure authentication logic |
| Logic Error | Identify incorrect business calculations |

---

### Stage 3 – Debugging Challenge

Participants will receive only the buggy version of the system.

They will:

- Run the system  
- Observe incorrect behavior  
- Use Claude AI to analyze the issue  
- Identify root causes  
- Implement fixes  

Their debugging process and AI interactions will be documented.

## 3. System Architecture

The system follows a **modular pipeline architecture**, where each component performs a specific responsibility.

### Architecture Components

| Module | Responsibility |
|------|------|
| `main.py` | Entry point that orchestrates transaction processing |
| `validation.py` | Validates transaction structure and required fields |
| `security.py` | Verifies API token authentication |
| `fee.py` | Calculates transaction processing fees |
| `audit.py` | Records transaction logs and audit data |

---

## 4. System Workflow

The system processes transactions through a **sequential pipeline**.

### Processing Steps

1. Transaction request is received  
2. Input validation checks transaction structure  
3. Security module verifies API token  
4. Fee module calculates transaction fee  
5. Audit module records the transaction  
6. System returns transaction result  

---

## 5. Processing Flow Diagram

```
Transaction Input
        |
        v
  validation.py
        |
        v
   security.py
        |
        v
     fee.py
        |
        v
    audit.py
        |
        v
Transaction Result
```
This pipeline ensures **separation of responsibilities**, making debugging easier.

## 6. Defect Injection Strategy

Defects will be distributed across system modules.

| Defect ID | Module | Category | Description |
|-----------|--------|----------|-------------|
| SN-01 | `audit.py` | Silent Failure | Exception swallowed by `except: pass` |
| SN-02 | `validation.py` | State Mutation | Input list mutated during validation |
| SN-03 | `security.py` | Security Vulnerability | Token compared using `==` |
| SN-04 | `fee.py` | Logic Error | Incorrect fee calculation |


## 7. Defect Scenarios

### SN-01 – Silent Failure in Audit Logging

**Module:** `audit.py`  
**Category:** Silent Failure  
**Severity:** Critical  
**Root Cause:** Exception swallowed using `except: pass`

---

## Example

Consider a **payment gateway system** processing thousands of transactions per minute.

A transaction is successfully processed:

- **Transaction ID:** TXN10283  
- **Amount:** ₹5000  
- **Status:** SUCCESS  

However, due to a temporary database issue, the **audit logging fails**. Because the exception is silently ignored, the transaction is **never recorded in the audit logs**.

Later during **financial reconciliation**:

- Finance teams cannot locate the transaction in audit logs  
- Compliance teams cannot trace the transaction history  
- The system appears to have lost transactions  

This type of defect is extremely dangerous because the system **appears to work correctly while silently losing critical operational data**.

---

## Correct Fix

Replace the silent exception with **explicit error handling**.

```
python
except Exception as e:
    logger.error(f"Audit logging failed: {e}")
    raise
 id="pmzog4"
```

## How Participants Will Notice the Defect

Participants will execute the transaction system with the provided dataset.

### Example Transaction

- **Transaction ID:** TXN10283  
- **Amount:** ₹5000  
- **Status:** SUCCESS  

The system reports that the transaction was processed successfully.

However, when participants inspect the **audit logs**, they may notice that some transactions are missing.

### Example Audit Log
```
TXN10281
TXN10282
TXN10284
```

Transaction **TXN10283** is missing even though it was processed successfully.

This inconsistency indicates that the **audit logging system may not be recording all transactions**.

---

## Participant Investigation

Participants will trace the **transaction pipeline**:

```
Transaction Input
        |
        v
  validation.py
        |
        v
   security.py
        |
        v
     fee.py
        |
        v
    audit.py

```


Since the issue involves **missing logs**, they will inspect the **`audit.py` module**.

Inside the code they may find the following implementation:

```
python
try:
    write_to_audit_store(transaction)
except:
    pass
```

At this point participants may suspect that errors during audit logging are being silently ignored.

----

## SN-02 – State Mutation in Transaction Validation

**Module:** `validation.py`  
**Category:** State Mutation  
**Severity:** High  
**Root Cause:** Input list modified during validation without defensive copy

---

### Example:

Consider a **payment gateway system** processing batch transactions from merchants.

A merchant submits a batch request:

- **Batch ID:** BATCH4582

### Transactions
```
- **TXN1001** – Amount: ₹100.50  
- **TXN1002** – Amount: ₹250.75  
- **TXN1003** – Amount: ₹75.99
```

During validation, the system converts transaction amounts to integers for format checking.
```
100.50 → 100
250.75 → 250
75.99 → 75
```

However, the **validation module modifies the original transaction objects directly** instead of working on a copy.

Later in the processing pipeline, the **fee calculation module receives modified values**, resulting in incorrect fee calculations.

### Example

- **Original amount:** ₹100.50  
- **Correct fee (2%):** ₹2.01  

After mutation:

- **Modified amount:** ₹100  
- **Calculated fee:** ₹2.00  

While the difference seems small, at scale it creates **financial discrepancies across large transaction volumes**.

---

### Correct Fix

Use **defensive copying** to prevent modifying original data.
```
python

transactions_copy = copy.deepcopy(transactions)
 id="q07xvo"
```

### Participant Investigation

Participants trace the **transaction pipeline** to determine where the modification occurs.

validation → security → fee → audit


Since the amount appears to change **before fee calculation**, they investigate **`validation.py`**.

Inside the validation module they may find code similar to:
```
python
for txn in transactions:
    txn["amount"] = int(txn["amount"])
```
Participants may compare the expected transaction values with the values observed during fee calculation.

| Transaction ID | Expected Amount | Actual Amount Used by System |
|----------------|----------------|------------------------------|
| TXN1001 | ₹100.50 | ₹100 |
| TXN1002 | ₹250.75 | ₹250 |
| TXN1003 | ₹75.99 | ₹75 |
---

## SN-03 – Insecure Token Comparison

**Module:** `security.py`  
**Category:** Security Vulnerability  
**Severity:** High  
**Root Cause:** Token compared using `==`

---

## Example:

Consider a **payment gateway API** used by merchants to submit transactions.

### Example Request
```
- Merchant ID: M102  
- API Token: ABF23D89XK92  
- Transaction ID: TXN20384  
- Amount: ₹3500  
```
The **security module verifies the API token** before processing the transaction.

## Authentication Logic

The authentication logic compares tokens directly.
```
python
if provided_token == expected_token
```

This approach introduces a timing attack vulnerability.

Attackers can send repeated requests with partial token guesses and measure response time differences to reconstruct the correct token.

Once the token is discovered:

- Attackers may submit fraudulent transactions
- Unauthorized systems can access the payment API
- Security breaches may occur

## Correct Fix

Use **constant-time comparison**.
```
python
import hmac

hmac.compare_digest(provided_token, expected_token)
```

### How Participants Will Notice the Defect

This defect is intentionally subtle.

Participants running the system will observe:

- Transactions with valid tokens succeed  
- Transactions with invalid tokens fail  
- No visible errors in logs  

So initially, nothing appears wrong.

The defect becomes noticeable only when participants inspect the **authentication implementation in the security module**.

While reviewing `security.py`, they may see:
```
python
if provided_token == expected_token
```

At this point participants may begin questioning:

- Is direct token comparison secure?
- Are there recommended security practices for comparing authentication tokens?
- Could this introduce a vulnerability?

Participants may then consult Claude AI to analyze the code.

----

## SN-04 – Fee Calculation Rounding Error

**Module:** `fee.py`  
**Category:** Logic Error  
**Severity:** Medium  
**Root Cause:** Integer arithmetic used in financial calculation

---

### Example:

Consider a **digital payment platform** charging a **2% processing fee**.

### Example Transaction
```
Transaction ID: TXN30921
Amount: ₹199.99  
Processing Fee: 2%
```
### Correct Calculation
```
199.99 × 2% = 3.9998
Rounded Fee = ₹4.00
```
### System Calculation

```
python
fee = int(amount * 0.02)
```

Result
```
int(3.9998) = 3
```

The system undercharges the fee.

Across thousands of transactions:
```
Loss per transaction: ₹1
Transactions per day: 100,000
Daily loss: ₹100,000
```

## Correct Fix

Use **precise decimal arithmetic**.
```
python
from decimal import Decimal

fee = Decimal(amount) * Decimal("0.02")
```

## 8. System Artifacts

The POC maintains three versions of the system.

| Artifact | Description |
|----------|-------------|
| Base Code | Clean and correct system implementation |
| Buggy Code | Version containing injected defects |
| Solution Code | Internal reference implementation |

The **buggy version** will be provided to participants, while the **solution version remains internal**.

## 9. AI Collaboration Workflow

Participants will use **Claude AI** during debugging.

### Typical Workflow

1. Engineer observes system failure  
2. Engineer writes prompt to Claude  
3. Claude suggests possible fixes  
4. Engineer evaluates the suggestion  
5. Engineer modifies or implements solution  
6. Engineer documents the interaction  

This process measures **AI collaboration effectiveness**.

## 10. Expected Outcomes

- Effectiveness of AI-assisted debugging  
- Engineer ability to analyze system architecture  
- Quality of AI collaboration  
- Accuracy of bug diagnosis


## 11 How Claude Code Is Used in This Hackathon
This hackathon is conducted entirely using Claude Code — the CLI-based AI engineering tool. Participants interact with Claude directly from their terminal while working inside the SoloNode codebase. This section explains what a Claude declaration is, how declarations map to each stage of the 4-hour assessment, example declarations for each deliverable, and the rules that govern how Claude may be used throughout the session.


## Claude Declaration Structure

Every declaration follows a **four-part structure**:

### 1. Role
Tell Claude what kind of expert it is acting as.  
**Example:**  
> “You are a senior Python engineer.”

---

### 2. Context
Describe the situation and the specific symptom observed.  
**Example:**  
> “I am working on SoloNode, a Python transaction audit service. When I run the system, some transactions are reported as successful but never appear in the audit log.”

---

### 3. Task
State exactly what you want Claude to do.  
**Example:**  
> “Review the `audit.py` module I have pasted below and identify what is causing this behaviour.”

---

### 4. Output Format
Specify what the response should look like.  
**Example:**  
> “Name the defect category, explain the root cause, and provide a corrected version of the function.”

---

## Stage 1 Declarations 

The participant explores SoloNode, identifies all defects, writes CLAUDE.md, and produces DIAGNOSIS.md. Claude declarations in this stage are symptom-driven — the participant does not know what defects exist or how many. Every declaration must start from what the participant actually observes when running the system.

**Declaration 1A**

To rapidly understand the SoloNode architecture before diving into individual modules.

>“You are a senior Python engineer onboarding onto an unfamiliar codebase. I have just been handed SoloNode, a transaction audit microservice. The original developer has left. There are no tests. I will paste the file listing and contents of each module below. Read the entire codebase, explain the data flow from input to output, identify the responsibility of each module, and flag anything that looks structurally suspicious or unusual. Do not fix anything yet — only describe what you see.”


**Declaration 1B — Symptom-Driven Module Investigation**

Use when a specific symptom has been observed (e.g. missing audit log entries, incorrect fee values). Scope this declaration to one module at a time.

>“You are a Python debugging expert. I am running SoloNode and I observe the following: [describe the symptom exactly as seen — do not guess the cause]. I have pasted the [module name] below. Read through the code, reason through what could produce this specific symptom, name the category of defect if one exists, and explain the root cause. Do not assume — base your answer only on the code provided.”


**Declaration 1C — CLAUDE.md Drafting**

Use after completing the initial exploration to draft CLAUDE.md.It must reflect the participant’s own understanding — not a copy of Claude’s output. Use Claude to structure it but write the content yourself.

>“You are a technical documentation specialist. I need to produce a CLAUDE.md file for the SoloNode codebase. This file will be read by a new developer who has never seen the code. It must include: project purpose and architecture in plain language, all modules and their responsibilities, all run and test commands, the defects I have found so far with their locations and root causes, and specific guidance on what kinds of prompts work well and poorly for this codebase. I will provide the codebase and my current notes. Generate a structured CLAUDE.md template that I can then fill in with my own observations.”


**Declaration 1D — DIAGNOSIS.md Entry Drafting**

Use after identifying each defect to produce a well-structured DIAGNOSIS.md entry. DIAGNOSIS.md is assessed live by the assessor at Checkpoint 1 (09:45). Each entry must show the participant understands the production impact of the defect — not just that it exists.

>“You are a senior engineer writing a defect report for a production incident review. I have identified a defect in SoloNode. Here are my notes: [paste your findings]. Help me write a DIAGNOSIS.md entry for this defect that includes: defect ID, module affected, defect category, exact location in code, root cause explanation in plain language, what would happen in a live production environment if this was never fixed, and my proposed fix approach. Do not write the fix code yet — only the diagnosis entry.”


## Stage 2 Declarations

The participant fixes all 4 defects and writes tests that fail before the fix and pass after. Claude declarations in this stage are fix-focused and test-focused. The participant is expected to critically evaluate Claude’s suggestions — not accept them as-itis. The target correction ratio is 25–35%, meaning participants should modify or reject roughly one in three to four Claude suggestions, with documented reasoning in LOG_SUBMISSION.md.

**Declaration 2A — Fix Generation (one defect at a time)**

>“You are a Python engineer implementing a targeted bug fix. The defect is: [state the root cause in your own words, referencing your DIAGNOSIS.md entry]. The affected function is [function name] in [module name]. Constraints: the fix must be minimal — change only what is necessary to resolve the root cause. Do not refactor surrounding code. Do not introduce new dependencies unless essential. Provide the corrected function only, with a one-line comment explaining what was changed and why.”


**Declaration 2B — Test Writing**

Use after each fix to write a test that proves the defect existed. The test must fail on the buggy version and pass on the fixed version.

>“You are a Python test engineer writing a regression test using pytest. The defect I just fixed is: [describe the defect and the fix in one sentence]. Write a single focused test that: (1) would fail if run against the original buggy code, (2) passes after my fix, and (3) tests the specific behaviour that was broken — not just that the function runs without error. Include a docstring explaining what the test proves.”


## Stage 3 Declarations — Agentic Pipeline

**Declaration 3A — Pipeline Design**

>“You are a Python automation engineer. I need to build pipeline.py — a standalone script that: (1) reads a JSON file containing a batch of transaction records, (2) passes each transaction through SoloNode’s validation and processing logic using the fixed modules, (3) separates records into passing and failing outputs, and (4) writes each group to a separate JSON file. The pipeline must run with a single command and require no manual steps. I have pasted the current SoloNode module structure below. Design the pipeline architecture first — do not write code yet. Describe the data flow, the inputs, the outputs, and any error handling strategy.”


**Declaration 3B — Pipeline Implementation**

>“You are a Python engineer implementing the pipeline we just designed. Using the architecture described above, write pipeline.py. Requirements: use only Python standard library imports, handle missing or malformed transaction records without crashing, log each transaction’s outcome clearly, and produce two output files: passing_transactions.json and failing_transactions.json. The script must be runnable with: python pipeline.py transactions.json”


## Claude Declarations by Observed Symptom

Participants are not told what defects exist or what category of defect they are looking for. The following declarations are examples of how a participant should approach Claude once they observe something unexpected while running the system. The goal of each declaration is for Claude to help the participant discover, categorize, and understand the defect on their own.


Each example below shows: the symptom the participant observes, the declaration they write to Claude, and what Claude is expected to help them discover.

---

**Declaration 1 — Module: audit.py**

**Observed Symptom:** The participant runs the system and processes several transactions. The system reports all transactions as successful, but when the participant checks the audit logs, some transaction IDs are missing. No errors are printed anywhere.

**Example Declaration to Claude:**

>“You are a Python debugging expert. I am running a transaction processing system and I notice that some transactions are not appearing in the audit logs, even though the system says they were processed successfully. There are no error messages or exceptions printed anywhere. I have pasted the audit.py module below. Can you review this code, tell me what type of issue this could be, and explain why this kind of problem is difficult to detect? Do not assume what the defect is — reason through the code and identify it.”


**What Claude Will Help the Participant Discover:** Claude will analyze the code, identify the problematic pattern, name the defect category, explain why this class of issue is dangerous in production systems, and guide the participant toward a correct fix — without the participant needing to know any of this in advance.

---

**Declaration 2 — Module: validation.py**

**Observed Symptom:** The participant submits a batch of transactions with decimal amounts. The system processes them, but the calculated fees are slightly lower than expected. When the participant compares the original input values against the values received by the fee module, the amounts appear to have changed.

**Example Declaration to Claude:**
>“You are a Python systems analyst. I have a transaction processing pipeline with multiple stages: validation, security, fee calculation, and audit. I noticed that the transaction amounts entering the fee module are different from the amounts I originally submitted. The validation stage runs before fee calculation. I have pasted validation.py below. Can you read through this code and explain what might be causing the input data to change between pipeline stages? What category of software defect does this fall under?”

**What Claude Will Help the Participant Discover:** Claude will trace how data flows through the validation function, identify whether the original input is being modified, name the defect category, and recommend safe data handling practices — all based purely on the observed symptom the participant described.

---

**Declaration 3 — Module: security.py**

**Observed Symptom:** The participant reviews the authentication module and finds it appears to work correctly — valid tokens are accepted and invalid tokens are rejected. However, something about the implementation feels unusual when they read the code carefully. There are no visible errors or output differences.

**Example Declaration to Claude:**

>“You are a code security reviewer. I am reviewing a Python authentication module that checks API tokens before processing transactions. The system seems to work — it accepts correct tokens and rejects wrong ones — but I want to make sure the implementation is secure. I have pasted security.py below. Please review the token comparison logic and tell me whether this implementation has any security concerns, even if the system appears to be functioning correctly. What category of vulnerability, if any, does this fall under?”

**What Claude Will Help the Participant Discover:** Claude will analyze the comparison logic, explain what vulnerability category applies, describe how an attacker could exploit it even when the system appears functional, and recommend the secure alternative — teaching the participant a security concept they may not have previously encountered.

---

**Declaration 4 — Module: fee.py**

**Observed Symptom:** The participant manually calculates the expected fee for several transactions and compares them against what the system produces. For whole-number amounts the fee looks correct, but for transactions with decimal amounts the calculated fee is consistently lower than expected by a small amount.

**Example Declaration to Claude:**

>“You are a Python code reviewer. I have a fee calculation module that is supposed to apply a 2% processing fee to each transaction. When I manually calculate the expected fee and compare it against the system output, I find the system always produces a slightly lower fee than expected, but only for transactions with decimal amounts. Whole number amounts seem fine. I have pasted fee.py below. Can you review the calculation logic, tell me what type of defect this is, and explain why it happens specifically with decimal values?”

**What Claude Will Help the Participant Discover:** Claude will identify the arithmetic issue in the calculation, explain what category of logic error this is, show why it affects only decimal values, quantify the financial impact at scale, and recommend the correct Python approach for precise financial arithmetic.

The declarations above are examples to illustrate the expected format and approach. Participants are encouraged to write their own declarations based on what they actually observe when running the system. Declarations that accurately describe the symptom without guessing the defect in advance will yield the most useful responses from Claude.

---

## 12 . Claude Code CLI Features Used

>This hackathon is conducted using Claude Code — Anthropic’s command-line AI engineering tool. Participants interact with Claude directly from their terminal alongside the codebase. This section explains each Claude Code CLI feature that participants may use during the challenge, and what they are expected to report in their submission.


**CLI Features and How They Are Used in This Hackathon**

**1 Subagents**

**What it is:** Claude Code can launch subagents — separate, scoped Claude instances — to handle a specific task in parallel or in isolation, without polluting the main session context. Each subagent operates with its own focused scope.

**How participants use it in this hackathon:** A participant can launch a subagent scoped only to audit.py to analyze logging behavior, while keeping their main session focused on tracing the overall pipeline. This enforces the single-module declaration discipline and prevents context bleed between modules.

**What to report in submission:** Which modules did you open subagents for? What task did each subagent handle? Did using a subagent produce a more focused or useful response compared to your main session?

---

**2 Plugins (MCP Servers)**

**What it is:** Claude Code supports MCP (Model Context Protocol) plugins — external server integrations that give Claude access to tools beyond the file system, such as databases, APIs, browsers, or custom tooling. Plugins are declared in the Claude Code configuration and become available as tools Claude can invoke during a session.

**How participants use it in this hackathon:** If a participant configures a plugin such as a log viewer or a test runner, Claude can invoke it directly to inspect live audit log output or run the transaction pipeline and capture results — reducing the need for the participant to copy-paste outputs manually into declarations.

**What to report in submission:** Which plugins, if any, did you configure? What did each plugin allow Claude to do that it could not do otherwise? Did plugin use improve the quality or speed of your debugging?

---

**3 Skills (Custom Slash Commands)**

**What it is:** Skills in Claude Code are reusable prompt templates stored as markdown files in the .claude/commands/ directory and invoked as custom slash commands (e.g. /debug-module or /security-review). They allow participants to define a structured declaration once and reuse it consistently across modules without retyping the full prompt each time.

**How participants use it in this hackathon:** A participant might create a skill such as /symptom-analysis that always instructs Claude to act as a debugging expert, describe the symptom observed, read the specified module, identify the defect category, and suggest a fix — applied consistently to each module they investigate.

**What to report in submission:** Did you create any custom slash commands? Paste the skill template you wrote. How many times did you invoke it and for which modules?

---

**4 Resume (--continue / --resume)**

**What it is:** Claude Code sessions can be resumed after interruption using claude --continue (resumes the most recent session) or claude --resume (presents a list of past sessions to choose from). Resuming restores the full conversation history and file context so participants can continue exactly where they left off without re-explaining the problem.

**How participants use it in this hackathon:** If a participant pauses between investigating modules and returns later, they can resume their session and Claude will remember the full debugging context — which modules were already investigated, what symptoms were observed, and what fixes were applied — without needing to repeat any of it.

**What to report in submission:** Did you use --continue or --resume at any point? How many separate sessions did your debugging span? Did resuming a session save you time or improve continuity?

---

### 13. Approximate Token Usage

>Token usage is a measure of how much of Claude’s processing capacity a participant consumed during their hackathon session. Every declaration sent to Claude and every response received costs tokens. Tracking token usage teaches participants to think about AI collaboration economically — not just whether Claude helped, but how efficiently they used it.


**13.1 How to Find Your Token Usage**

>At the end of your hackathon session, token usage can be found in two places. First, Claude Code displays a running token count at the end of each response in the terminal. Second, the full session cost is visible in the Anthropic Console usage dashboard atconsole.anthropic.com under Usage. Participants should note their total token count at the end of the session before submitting.


**13.2 What to Report**

Participants must include the following in their submission under the heading “Approximate Token Usage”:

**Total tokens used:** The approximate total from the usage dashboard at the end of the session. Example: ~18,400 tokens.

**Most valuable interaction:** Which single declaration produced the most useful response relative to its cost? Quote the declaration and explain what made it high-value.

**Least valuable interaction:** Which declaration consumed tokens without producing useful output? What would you write differently next time?

**Reflection:** In one or two sentences — was your token usage well spent? Did you get proportionate value from Claude relative to the tokens consumed?


**13.3 Token Efficiency Guidance**

High token usage is not penalized, but low-efficiency usage is. The following patterns waste tokens and should be avoided:

***1. Vague Declarations***
Declarations such as:

- “fix my code”
- “what is wrong?”

without providing sufficient **context** force Claude to ask clarifying questions.  
This consumes additional **turns and tokens** before any useful output can be produced.

---

***2. Pasting Entire Codebases***

Pasting an entire codebase into a single declaration:

- Floods the **context window** with irrelevant content
- Reduces the **precision of Claude’s response**
- Consumes significantly **more tokens**

A **focused, single-module declaration** is usually much more effective.

---

***3. Repeating the Same Declaration***

Repeating the **same declaration multiple times** without changing the approach after receiving an unsatisfactory response:

- Multiplies **token cost**
- Does **not improve outcomes**

Instead, **refine the declaration** based on Claude’s previous response to guide the AI toward a better result.

