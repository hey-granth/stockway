"""
Order state management and validation for secure state transitions
"""

from typing import Dict, Set, Optional
import logging
from core.exceptions import InvalidStateTransitionError

logger = logging.getLogger(__name__)


class OrderStateManager:
    """
    Manager for validating and enforcing order state transitions
    """

    # Define valid state transitions
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "pending": {"accepted", "rejected", "cancelled"},
        "accepted": {"assigned", "cancelled"},
        "assigned": {"in_transit", "cancelled"},
        "in_transit": {"delivered", "cancelled"},
        "delivered": set(),  # Terminal state
        "rejected": set(),  # Terminal state
        "cancelled": set(),  # Terminal state
    }

    # Define which roles can perform which transitions
    ROLE_PERMISSIONS: Dict[str, Dict[str, Set[str]]] = {
        "SHOPKEEPER": {
            "pending": {"cancelled"},
            "accepted": {"cancelled"},
        },
        "WAREHOUSE_MANAGER": {
            "pending": {"accepted", "rejected"},
            "accepted": {"assigned"},
        },
        "RIDER": {
            "in_transit": {"delivered"},
        },
        "ADMIN": {
            # Admins can perform any valid transition
            "pending": {"accepted", "rejected", "cancelled"},
            "accepted": {"assigned", "cancelled"},
            "assigned": {"in_transit", "cancelled"},
            "in_transit": {"delivered", "cancelled"},
        },
    }

    @classmethod
    def validate_transition(
        cls, current_state: str, new_state: str, user_role: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a state transition is allowed

        Args:
            current_state: Current order state
            new_state: Desired new state
            user_role: Role of user attempting transition

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if transition is valid in general
        if current_state not in cls.VALID_TRANSITIONS:
            return False, f"Invalid current state: {current_state}"

        valid_next_states = cls.VALID_TRANSITIONS[current_state]

        if new_state not in valid_next_states:
            return (
                False,
                f"Cannot transition from '{current_state}' to '{new_state}'. Valid transitions: {', '.join(valid_next_states) if valid_next_states else 'none (terminal state)'}",
            )

        # Check if user role has permission for this transition
        if user_role not in cls.ROLE_PERMISSIONS:
            return False, f"Invalid user role: {user_role}"

        role_transitions = cls.ROLE_PERMISSIONS[user_role]

        if current_state not in role_transitions:
            return (
                False,
                f"Role '{user_role}' cannot modify orders in '{current_state}' state",
            )

        if new_state not in role_transitions[current_state]:
            return (
                False,
                f"Role '{user_role}' cannot transition order from '{current_state}' to '{new_state}'",
            )

        return True, None

    @classmethod
    def can_transition(cls, current_state: str, new_state: str, user_role: str) -> bool:
        """
        Check if transition is allowed (boolean version)

        Args:
            current_state: Current order state
            new_state: Desired new state
            user_role: Role of user attempting transition

        Returns:
            True if transition is allowed, False otherwise
        """
        is_valid, _ = cls.validate_transition(current_state, new_state, user_role)
        return is_valid

    @classmethod
    def get_allowed_transitions(cls, current_state: str, user_role: str) -> Set[str]:
        """
        Get list of allowed transitions for current state and user role

        Args:
            current_state: Current order state
            user_role: Role of user

        Returns:
            Set of allowed next states
        """
        if current_state not in cls.VALID_TRANSITIONS:
            return set()

        if user_role not in cls.ROLE_PERMISSIONS:
            return set()

        # Get valid next states based on role
        if current_state in cls.ROLE_PERMISSIONS[user_role]:
            return cls.ROLE_PERMISSIONS[user_role][current_state]

        return set()

    @classmethod
    def log_transition(
        cls,
        order_id: int,
        user_id: int,
        from_state: str,
        to_state: str,
        reason: Optional[str] = None,
    ):
        """
        Log state transition for audit trail

        Args:
            order_id: Order ID
            user_id: User ID performing transition
            from_state: Previous state
            to_state: New state
            reason: Optional reason for transition
        """
        logger.info(
            f"Order state transition",
            extra={
                "order_id": order_id,
                "user_id": user_id,
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
            },
        )
