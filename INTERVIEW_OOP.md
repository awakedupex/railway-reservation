# OOP Interview Q&A

## SOLID Principles

### Q: Explain the Single Responsibility Principle. Where did you apply it?

**A:** A class should have exactly one reason to change. In this project:
- `BookingService` handles only booking orchestration (reserve → confirm → cancel)
- `PricingStrategy` implementations handle only price calculation
- `BookingState` implementations handle only status transitions

If pricing rules change, I modify `Strategy` classes. If booking logic changes, I modify `BookingService`. Never both.

### Q: How did you apply the Open-Closed Principle?

**A:** Classes are open for extension but closed for modification.
- **Strategy Pattern**: To add Senior Citizen pricing, I write a new class `SeniorCitizenPricing(PricingStrategy)` — zero changes to `PricingContext` or existing strategies.
- **State Pattern**: To add a `REFUNDED` state, I write `RefundedState(BookingState)` — no existing state classes change.

### Q: Where is Liskov Substitution used?

**A:** Any `PricingStrategy` implementation can be swapped into `PricingContext` without breaking behavior. `StudentDiscountPricing` and `StandardPricing` are both substitutable for the `PricingStrategy` interface.

### Q: Interface Segregation in your code?

**A:** The `BookingState` interface has exactly two methods (`confirm`, `cancel`) — no method is forced on a class that doesn't need it. `CancelledState` implements both because every state must handle both transitions.

### Q: Dependency Inversion — high-level modules shouldn't depend on low-level modules?

**A:** `BookingService` depends on the `PricingStrategy` *abstract interface*, not on concrete classes like `StudentDiscountPricing`. The concrete strategy is injected at runtime via the `PricingContext`.

---

## Encapsulation

### Q: Where did you use encapsulation?

**A:** The `PricingContext` hides its internal strategy implementation. Callers call `get_price(base_price)` without knowing whether a discount is being applied. Similarly, `BookingState` subclasses encapsulate the validation logic for each transition — callers don't see if/else checks.

---

## Inheritance & Polymorphism

### Q: Where is polymorphism used?

**A:** The `BookingState` interface is polymorphic — `PendingState`, `ConfirmedState`, and `CancelledState` all implement `confirm()` and `cancel()` differently. The same method call (`state.confirm()`) behaves differently depending on the runtime type. This is runtime polymorphism.

### Q: Why not just use an enum and if/else blocks?

**A:**
```python
# Bad — every status change requires editing this method
def transition(status, action):
    if status == "PENDING" and action == "confirm":
        return "CONFIRMED"
    elif status == "CONFIRMED" and action == "confirm":
        raise Error("Already confirmed")
    # ... grows linearly with states × actions
```

**State Pattern eliminates this.** Each transition is a single method call, and invalid transitions raise errors automatically because the behavior is distributed across state classes. Adding a new state means adding a file, not modifying a chain of if/else.

---

## Design Pattern: Strategy

### Q: When would you use Strategy vs a simple if-else?

**A:** Strategy when:
1. Algorithms change frequently or new ones are added
2. Algorithms are selected at runtime
3. You want to unit-test each algorithm independently

If-else is fine for 2-3 fixed, never-changing options. Strategy is better when the number of variants grows or when they change independently.

### Q: What if you have 50 pricing strategies?

**A:** Strategy still works — each is its own class. I'd use a registry pattern with a dictionary mapping user types to strategy instances (like the `USER_TYPE_STRATEGY` dict in `booking.py`). You could also load strategies from config or via plugin discovery.

---

## Design Pattern: State

### Q: State vs Strategy — what's the difference?

**A:** Both use composition and a shared interface, but their intent differs:
- **Strategy**: Encapsulates interchangeable *algorithms* (how to calculate a price)
- **State**: Encapsulates behavior that changes based on *internal state* (what transitions are valid)

In State, the context's state typically *changes* at runtime (booking goes PENDING → CONFIRMED). In Strategy, the strategy is typically set once or swapped explicitly.

### Q: Your State Pattern only returns strings — is that a pure implementation?

**A:** It could be cleaner by having the state mutate the booking object directly. For an interview, I'd explain: "The state classes return the new status string, and the service applies it. A purer implementation would pass the booking object to the state method and let it set attributes. I chose this separation to keep state classes stateless and testable."

---

## General OOP

### Q: Difference between abstraction and encapsulation?

**A:** **Abstraction** hides complexity behind a simplified interface (e.g., `PricingStrategy` interface). **Encapsulation** restricts direct access to internal data (e.g., `PricingContext._strategy` is private).

### Q: Composition vs Inheritance — which do you prefer and why?

**A:** Favor composition over inheritance. `BookingService` *has a* `PricingContext` (composition) rather than `BookingService` *is a* `PricingStrategy` (inheritance). Composition is more flexible — you can swap strategies at runtime, test each component independently, and avoid deep inheritance hierarchies.

### Q: What would you add next to make this more OOP-compliant?

**A:**
- **Factory Pattern**: A `BookingFactory` to create booking objects with different initial states
- **Observer Pattern**: Notify users when booking status changes
- **Repository Pattern**: Abstract database access behind repository interfaces
