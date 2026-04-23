Defining what success means of this project.

    Catch fraud (recall) - “How many frauds did we stop?” - lossing fraud direct loss of money
    Avoid blocking real users (precision) - “How many genuine users did we wrongly block?” - False positive = lossing good customer
    Latency (VERY IMPORTANT in streaming) - “How fast do we decide?” - late = fraud already happened

    Success is maximizing fraud detection recall while minimizing false positives, under real-time latency constraints

Business Problem

    preventing financial loss without hurting genuine users

    Trade-off:
        Block transaction - Loss customer
        Allow transaction - loss money

    What system do:
        LOW RISK → allow  
        MEDIUM RISK → review / OTP  
        HIGH RISK → block

    The goal is to prevent financial loss while preserving user experience by making risk-based decisions rather than binary classifications.
        
Why ML and not SQL? / Why probabilistic and not a heuristic (Simple pattern = known rules)?

    combine multiple weak signals
    learn patterns
    adapt behavior
    generalize

    Fraud signals are weak individually but strong when combined. ML captures these interactions better than rule-based or SQL systems.

What happens when data changes?

    In fraud systems data changes are:
        user behavior evolves
        fraud patterns change
        seasonality (festivals, sales)
        new attack types

    Where system breaks?
        Data + Concept Drift: 
            example:
                earlier: avg spend = ₹1000
                now: avg spend = ₹5000 (sale season)

                    Solved by ( profile.avg_amount → continuously updated )

        Monitoring drift:
            We must track:
                avg amount distribution
                fraud rate over time
                feature distributions

        Retraining Loop:
            logged features → detect drift → retrain model → redeploy

How to handle edge cases?

    New user (cold start)
        txn_count < threshold → low confidence decision

    Missing Redis data:
        fallback defaults:
            avg_amount = current amount
            velocity = 0

    Divide by zero:
        Divide by zero
            amount / avg
        Fix:
            amount / (avg + 1e-5)

    Geo missing:
        No last loaction
            speed = 0 (safe default)

    Stream lag / failure:
        Consumer stops:
            Redis keeps data
            consumer resumes from last_id

What if predictions are wrong?
    Your system WILL:
        block real users
        allow fraud sometimes

        instead of:
            fraud / not fraud
        we do:
            LOW → allow  
            MEDIUM → OTP / step-up auth  
            HIGH → block 

    Feed back loop:
        wrong prediction → user complaint / chargeback → label update

    Monitoring errors
        Track:
            false positives
            false negatives

    Human-in-the-loop
        High-risk:
            send to review instead of blocking

Why this model and not others you tried?
    system has:
        tabular data
        mixed feature types
        non-linear interactions
        need for fast inference

    starting choice: Logistic Regression - Why?
        fast (milliseconds inference)
        interpretable
        easy to debug
        stable in production
    
    If model-upgrade required XGBoost / LightGBM. Why?
        captures nonlinear relationships
        better performance than LR
        still fast

    Why NOT deep learning
        overkill for tabular fraud data
        hard to debugand to explain to non-tech person
        latency higher
        data hungry

Tradeoff: Complexity vs Maintainability
    Logistic Regression
    Pros:
        easy to explain
        easy to debug
        stable
        low infra cost
    Cons:
        misses complex patterns

    XGBoost
    Pros:
        higher accuracy
        captures interactions
    Cons:
        harder to debug
        harder to monitor
        more tuning

    What I do basically:

    “I balance model complexity with maintainability by starting with simpler models for stability and observability, 
    and only introducing more complex models when they provide significant performance gains.”

Deployment constraints
    Latency
        decision must be < 100 ms
        no heavy computation

    eliminates:
        large deep models
        slow pipelines
        Real-time inference
        per event
        high throughput

    model must be:
        lightweight
        fast loading

    Memory constraints
        running inside consumer
        cannot load huge models

    Integration simplicity
        Python-based
        easy to plug into consumer
        
    So model must be:
        fast
        lightweight
        easy to serialize (.pkl)
        stable

What business metric improved and by how much?

    Real business metrics in fraud
    Fraud loss prevented
        money saved

    False positive rate
        how many real users you hurt

    Approval rate
        how many transactions go through

    Example:

    Assume:

        baseline (no system): ₹10,00,000 fraud/month
        new system catches 70%

    prevented:
        ₹7,00,000 saved

    But also:
        false positives = 3%
        means 3% users impacted

    “The system improved fraud detection recall from ~0 to ~70%, reducing estimated fraud loss by ~70%, 
    while maintaining false positives under ~3%.”

What’s the cost to run this system?
        “The system cost is driven primarily by Redis for state storage and the consumer service for real-time processing, 
        and scales with transaction throughput. For a moderate load system, 
        costs remain relatively low compared to the fraud loss prevented.”
    
How do we know it’s working in production?
    Fraud rate
        (fraud_detected / total_txns)

    sudden drop = model failing
    sudden spike = too aggressive

    False positives
        how many legit users blocked

    Model drift
        feature distribution changes
        avg amount shifts

    Latency
        decision time per txn
    Example
        Before:
            fraud caught = 50%

    After:
        fraud caught = 70%
        false positives = 3%
        latency = 20ms
    Feedback loop
        prediction → real outcome (chargeback) → compare → retrain

    “We monitor fraud rate, false positives, latency, and feature drift in production, 
    and use feedback from confirmed fraud cases to continuously evaluate and retrain the model.”

