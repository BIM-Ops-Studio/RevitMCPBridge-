# Batch Operations Strategy

## Overview
This document defines strategies for efficient batch operations through RevitMCPBridge, including transaction management, error recovery, and validation.

## Implemented Batch Methods (v1.0.10)

The following batch methods are now available in RevitMCPBridge:

### 1. executeBatch
The most powerful batch method - executes multiple different operations in a single transaction.

```json
{
  "method": "executeBatch",
  "params": {
    "operations": [
      { "method": "createWall", "params": { "startPoint": [0,0,0], "endPoint": [10,0,0], "levelId": 311, "height": 10 } },
      { "method": "createWall", "params": { "startPoint": [10,0,0], "endPoint": [10,10,0], "levelId": 311, "height": 10 } },
      { "method": "placeFamilyInstance", "params": { "location": [5,0,0], "typeId": 12345, "hostId": 67890 } }
    ],
    "transactionName": "Build Floor Plan",
    "rollbackOnError": true
  }
}
```

### 2. createWallBatch
Optimized for creating multiple walls with shared defaults.

```json
{
  "method": "createWallBatch",
  "params": {
    "walls": [
      { "startPoint": [0,0,0], "endPoint": [20,0,0] },
      { "startPoint": [20,0,0], "endPoint": [20,15,0] },
      { "startPoint": [20,15,0], "endPoint": [0,15,0] },
      { "startPoint": [0,15,0], "endPoint": [0,0,0] }
    ],
    "levelId": 311,
    "height": 10.0,
    "wallTypeId": 456
  }
}
```

### 3. placeElementsBatch
Optimized for placing multiple family instances (doors, windows, fixtures).

```json
{
  "method": "placeElementsBatch",
  "params": {
    "elements": [
      { "location": [5,0,0], "familyName": "Single-Flush", "typeName": "36\" x 84\"", "hostId": 123 },
      { "location": [15,0,0], "familyName": "Single-Flush", "typeName": "30\" x 84\"", "hostId": 124 },
      { "location": [10,15,0], "familyName": "Fixed", "typeName": "36\" x 48\"", "hostId": 125, "rotation": 180 }
    ]
  }
}
```

### 4. deleteElementsBatch
Delete multiple elements efficiently.

```json
{
  "method": "deleteElementsBatch",
  "params": {
    "elementIds": [12345, 12346, 12347, 12348]
  }
}
```

### 5. setParametersBatch
Set parameters on multiple elements.

```json
{
  "method": "setParametersBatch",
  "params": {
    "updates": [
      { "elementId": 123, "parameterName": "Mark", "value": "D-01" },
      { "elementId": 124, "parameterName": "Mark", "value": "D-02" },
      { "elementId": 125, "parameterName": "Comments", "value": "ADA Door" }
    ]
  }
}
```

## Performance Comparison

| Operation | Individual Calls | Batch Call | Improvement |
|-----------|-----------------|------------|-------------|
| Create 50 walls | ~5-10 seconds | ~0.5 seconds | 10-20x |
| Place 30 doors | ~3-6 seconds | ~0.3 seconds | 10-20x |
| Delete 100 elements | ~10 seconds | ~0.5 seconds | 20x |

## Current Architecture

### Single Transaction per Call
Currently, each MCP method call creates its own transaction:
```csharp
using (var trans = new Transaction(doc, "Operation"))
{
    trans.Start();
    // Single operation
    trans.Commit();
}
```

### Limitations
- Each call is independent
- No automatic rollback across calls
- Multiple round-trips for batch operations
- No atomic batch operations

## Batch Operation Patterns

### Client-Side Batching (Current Approach)
```python
# Call createWall multiple times
for wall_spec in walls:
    result = mcp_call("createWall", wall_spec)
    if not result["success"]:
        # Manual rollback if needed
        handle_error(result)
```

**Pros**: Simple, flexible
**Cons**: Many round-trips, no atomic rollback

### Server-Side Batching (Proposed Enhancement)
```python
# Single call with multiple operations
result = mcp_call("executeBatch", {
    "operations": [
        {"method": "createWall", "params": {...}},
        {"method": "createWall", "params": {...}},
        {"method": "placeFamilyInstance", "params": {...}}
    ],
    "rollbackOnError": True
})
```

**Pros**: Single transaction, atomic rollback
**Cons**: Requires new method implementation

## Recommended Batch Sizes

| Operation | Recommended Batch | Max Batch | Notes |
|-----------|------------------|-----------|-------|
| createWall | 20-30 | 100 | Memory for undo stack |
| placeFamilyInstance | 20-30 | 100 | Door/window placement |
| setParameter | 50-100 | 500 | Lightweight operation |
| deleteElements | 50-100 | 200 | Watch for dependencies |

## Transaction Strategy

### For Small Batches (< 20 elements)
```
1. Call methods individually
2. Track element IDs as placed
3. On error: delete placed elements manually
4. Verify count at end
```

### For Medium Batches (20-100 elements)
```
1. Group by type (all walls, then all doors)
2. Process each group
3. Verify after each group
4. Continue or rollback based on group success
```

### For Large Batches (100+ elements)
```
1. Split into chunks of 50
2. Process chunk
3. Verify chunk
4. Save model (checkpoint)
5. Process next chunk
6. On failure: can restore to checkpoint
```

## Error Recovery

### Recovery Levels

#### Level 1: Retry
For transient errors (timeout, busy):
```python
for attempt in range(3):
    result = mcp_call(method, params)
    if result["success"]:
        break
    time.sleep(1)
```

#### Level 2: Skip and Continue
For non-critical failures:
```python
failed_elements = []
for element in elements:
    result = mcp_call("createWall", element)
    if not result["success"]:
        failed_elements.append(element)
        continue  # Skip this one
# Report failed elements at end
```

#### Level 3: Rollback
For critical operations:
```python
placed_ids = []
try:
    for element in elements:
        result = mcp_call("createWall", element)
        if result["success"]:
            placed_ids.append(result["elementId"])
        else:
            raise BatchError(f"Failed at element {element}")
except BatchError:
    # Rollback all placed elements
    mcp_call("deleteElements", {"elementIds": placed_ids})
```

### Checkpoint Pattern
```python
def batch_with_checkpoints(elements, checkpoint_size=50):
    """Process batch with checkpoint saves"""
    placed_ids = []

    for i, chunk in enumerate(chunks(elements, checkpoint_size)):
        # Process chunk
        for element in chunk:
            result = mcp_call("createWall", element)
            placed_ids.append(result["elementId"])

        # Checkpoint
        mcp_call("saveModel", {})  # If available
        store_checkpoint(i, placed_ids)

    return placed_ids
```

## Validation Integration

### After Each Batch
```python
def validate_batch(expected_count, category):
    """Validate batch was placed correctly"""
    result = mcp_call("getElementsByCategory", {"category": category})
    actual_count = len(result["elements"])

    return {
        "success": actual_count >= expected_count,
        "expected": expected_count,
        "actual": actual_count,
        "difference": actual_count - expected_count
    }
```

### Spot Check Pattern
```python
def spot_check(element_ids, expected_locations, tolerance=0.1):
    """Verify sample of elements at correct locations"""
    samples = random.sample(element_ids, min(5, len(element_ids)))

    for i, element_id in enumerate(samples):
        result = mcp_call("getElementLocation", {"elementId": element_id})
        actual = result["location"]
        expected = expected_locations[element_id]

        distance = calculate_distance(actual, expected)
        if distance > tolerance:
            return {"success": False, "element": element_id, "distance": distance}

    return {"success": True}
```

## Proposed Batch Methods

### executeBatch
```json
{
  "method": "executeBatch",
  "params": {
    "operations": [
      {"method": "createWall", "params": {...}},
      {"method": "createWall", "params": {...}}
    ],
    "transactionName": "Batch Wall Creation",
    "rollbackOnError": true,
    "continueOnWarning": true
  }
}

// Response
{
  "success": true,
  "results": [
    {"index": 0, "success": true, "elementId": 12345},
    {"index": 1, "success": true, "elementId": 12346}
  ],
  "summary": {
    "total": 2,
    "succeeded": 2,
    "failed": 0
  }
}
```

### createWallBatch
```json
{
  "method": "createWallBatch",
  "params": {
    "walls": [
      {"startPoint": [0,0,0], "endPoint": [10,0,0], "wallTypeId": 123},
      {"startPoint": [10,0,0], "endPoint": [10,10,0], "wallTypeId": 123}
    ],
    "levelId": 456,
    "height": 10.0
  }
}
```

### placeElementsBatch
```json
{
  "method": "placeElementsBatch",
  "params": {
    "elements": [
      {"familyName": "Single Flush", "typeName": "3'-0\"", "location": [5,0,0], "hostId": 789},
      {"familyName": "Single Flush", "typeName": "2'-8\"", "location": [15,0,0], "hostId": 790}
    ]
  }
}
```

## Performance Considerations

### Network Overhead
- Each MCP call: ~50-100ms overhead
- Batch of 100 individual calls: 5-10 seconds overhead
- Single batch call: ~100ms overhead
- **10-100x improvement with batching**

### Memory Management
- Large batches consume undo stack memory
- Revit may slow with very large transactions
- Balance batch size vs memory
- Consider periodic model saves

### Recommended Workflow
1. Query types once at start
2. Prepare all element specifications
3. Validate specs before sending
4. Send in optimized batches
5. Verify after each batch
6. Store results in memory

## Integration with Context Management

### Before Large Batch
```python
# Store what we're about to do
mcp__claude-memory__memory_store(
    content=f"Starting batch: {len(elements)} walls",
    project="CurrentProject",
    importance=6,
    memory_type="context"
)
```

### After Large Batch
```python
# Summarize outcome
mcp__claude-memory__memory_store(
    content=f"Created {success_count} walls. IDs: {first_id}-{last_id}",
    project="CurrentProject",
    importance=7,
    memory_type="outcome"
)

# Prune detailed results from context
# Keep only summary
```
