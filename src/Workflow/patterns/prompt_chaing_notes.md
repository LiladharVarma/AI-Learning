# Prompt Chaining: Turning One Big Task into Smaller Steps

Prompt chaining is a way to ask an AI model to do a task in stages. The answer from one step becomes the input to the next step. Each prompt has one clear job, which makes the workflow easier to understand and gives the program a chance to check the result before continuing.

Think of it like preparing a calendar invitation: first decide whether the message is asking for an event, then collect the details you need to create it.

## The basic idea

```text
User's request
      |
      v
Step 1: Understand or classify it
      |
      v
Check the result (a gate)
      |
      +---- Not an event / low confidence ----> Stop
      |
      v
Step 2: Extract the event details
      |
      v
Use the details in the application
```

This is more than sending the same request to the model twice. The steps have different responsibilities, and the program deliberately passes the useful result from the first step into the second.

## Our calendar example

The example lives in [`src/Workflow/patterns/prompt_chaining_1.py`](./src/Workflow/patterns/prompt_chaining_1.py). It uses Gemini and Pydantic response schemas to give each model call a specific output shape.

### Step 1: Decide whether it is a calendar request

`extract_event_info()` sends the user's text to Gemini and asks for an `EventExtraction` result. That result contains:

- `description`: the event description to use in the next step
- `is_calendar_event`: whether the request is about a calendar event
- `confidence`: how confident the classification is

For example, the request below should pass this first step:

```text
Let's schedule a 1h team meeting next Tuesday at 2pm with Alice and Bob
to discuss the project roadmap.
```

An email request, by contrast, should not be treated as a calendar event:

```text
Can you send an email to Alice and Bob to discuss the project roadmap?
```

### Step 2: Apply a gate before spending another model call

`process_calendar_request()` checks the first result:

```python
if not first.is_calendar_event or first.confidence < 0.7:
    return None
```

If the request is not a calendar event, or confidence is below `0.7`, the chain stops. Otherwise, it passes the extracted description to `parse_event_details()`:

```python
details = parse_event_details(first.description)
return details
```

That second call returns an `EventDetails` object with a name, date, duration, and participants. In short:

```text
Raw user text
    |
    v
extract_event_info()
    |
    +-- is_calendar_event is false, or confidence < 0.7 --> Stop
    |
    v
first.description
    |
    v
parse_event_details()
    |
    v
EventDetails(name, date, duration_minutes, participants)
```

The code uses `response_schema` for both calls, so each stage asks for structured data rather than relying on free-form prose. The first stage returns `EventExtraction`; the second returns `EventDetails`.

## Why split it into steps?

- **A focused prompt is easier to evaluate.** Classification and detail extraction are different jobs.
- **The gate avoids unnecessary work.** A likely non-event request does not trigger the detail-extraction call.
- **Structured outputs make results predictable.** The application can work with named fields instead of trying to interpret an arbitrary paragraph.
- **Failures are easier to locate.** You can inspect whether classification, the gate, or detail extraction produced an unexpected result.

## One detail about the current example

`EventConfirmation` is also defined in the Python file, but `process_calendar_request()` does not call a confirmation step yet. The active chain currently has two model calls: classify the request, then parse event details. A future step could use those details to generate a confirmation message or calendar link.

## When prompt chaining is useful

Use a chain when a task naturally breaks into steps, especially when later work depends on an earlier result or needs a check in between. Keep each step's goal and output clear. If a task is simple enough for one call, adding extra stages can make it slower and harder to maintain rather than better.
