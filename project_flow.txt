REAL-TIME FRAUD DETECTION SYSTEM — PROJECT FLOW

---

PROJECT OVERVIEW
We are building a real-time fraud detection system that simulates how modern payment systems detect suspicious transactions instantly before approval.
The focus is not just on machine learning, but on building a complete production-like system.

---

PHASE 1 — PROBLEM UNDERSTANDING

• Goal: Detect fraudulent transactions in real-time
• Objective: Reduce fraud loss while minimizing false alarms
• Constraint: System must respond within milliseconds (<100ms)
• Approach: Combine behavior tracking + rules + ML (later)

---

PHASE 2 — DATA SIMULATION (PRODUCER)

We built a realistic transaction simulator.

What it does:
• Generates user profiles (location, spending behavior, devices)
• Simulates real-world behavior (normal + fraud patterns)
• Models fraud lifecycle:

* CLEAN → normal user
* PROBING → small test transactions
* EXPLOITING → high-value fraud
* BURNED → account blocked

Each transaction includes:
• User ID
• Amount (local + USD)
• Country, latitude, longitude
• IP address
• Device ID
• Merchant info
• Fraud label (for training only)

Output:
• Stored in a JSONL file (transactions.jsonl)
• Sent to Redis stream (real-time pipeline)

---

PHASE 3 — DATA STORAGE STRATEGY

We implemented two parallel storage systems:

1. JSONL File (transactions.jsonl)
   • Used for:

   * Historical data
   * Model training
   * Debugging
   * Backfilling
     • Acts as long-term storage

2. Redis Stream
   • Used for:

   * Real-time data flow
   * Event processing
     • Acts as live pipeline between systems

---

PHASE 4 — STREAMING ARCHITECTURE

We introduced a streaming layer between producer and consumer.

Flow:
Producer → Redis Stream → Consumer

Why this is important:
• Handles high volume of data safely
• Prevents system crashes if consumer is slow
• Allows replay of past events
• Supports multiple consumers (scalable system)

---

PHASE 5 — BACKFILLING HISTORICAL DATA

We implemented a backfill process.

Purpose:
• Load existing 1 lakh (100,000) records into Redis
• Allow system to simulate past activity

Process:
• Read JSONL file
• Push each record into Redis stream

This ensures:
• Consumer can learn from past behavior
• System is not starting from empty state

---

PHASE 6 — REAL-TIME EVENT GENERATION

After backfill:
• Producer continuously generates new transactions
• Each transaction is:

* Written to JSON file
* Sent to Redis stream

This creates a continuous flow of data.

---

CURRENT SYSTEM STATUS

What is completed:

• Problem definition and business context
• Realistic fraud simulator (producer)
• JSON-based data storage
• Redis setup and integration
• Streaming pipeline (producer → Redis)
• Backfill capability for historical data

---

WHAT IS NOT BUILT YET (NEXT STEPS)

• Consumer (core system logic)

* Reads transactions from Redis
* Tracks user behavior over time
* Creates real-time features

• Feature Engineering (real-time)

* Transaction velocity
* Geo distance / travel speed
* Device/IP change detection
* Spending deviation

• Fraud Decision Engine

* Rule-based scoring
* ML model integration

• Monitoring & Metrics

* Latency (p50, p99)
* Fraud detection rate
* False positive rate

---

KEY ARCHITECTURE SUMMARY

Raw Flow:

JSON (historical data)
↓
Backfill
↓
Producer → Redis Stream → Consumer → Features → Decision

---

CORE IDEA

This project is not just about training a model.

It is about:
• Handling continuous data
• Tracking user behavior over time
• Making decisions instantly
• Designing a scalable system

---

END OF CURRENT PROJECT FLOW
