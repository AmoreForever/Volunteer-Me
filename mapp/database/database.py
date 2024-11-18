import os
import json
import abc
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum, auto
from contextlib import contextmanager

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from database.events import EventsDatabase


class UserRole(Enum):
    VOLUNTEER = auto()
    ORGANIZER = auto()


@dataclass
class UserProfile:
    username: str
    avatar: str
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[str] = None
    specializations: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    rating: Optional[list] = None


class SecurityManager:
    def __init__(self, time_cost: int = 4, memory_cost: int = 102400):
        """Advanced password hashing with configurable security parameters."""
        self._hasher = PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=8,
            hash_len=64,
            salt_len=32,
        )
        self._pepper = "salty_pepper_too_salty)))"

    def hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """Enhanced password hashing with optional salt."""
        salt = salt or os.urandom(16).hex()
        salted_password = f"{password}{salt}{self._pepper}"
        return self._hasher.hash(salted_password)

    def verify_password(self, stored_hash: str, password: str, salt: str) -> bool:
        """Secure password verification."""
        try:
            salted_password = f"{password}{salt}{self._pepper}"
            self._hasher.verify(stored_hash, salted_password)
            return True
        except VerificationError:
            logging.warning(f"Password verification failed for user")
            return False


class DatabaseManager(abc.ABC):
    """Abstract base class for database management."""

    @abc.abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """Save data to persistent storage."""
        pass

    @abc.abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load data from persistent storage."""
        pass


class JSONDatabaseManager(DatabaseManager):
    def __init__(self, filepath: str):
        """Initialize with file path and ensure directory exists."""
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def save(self, data: Dict[str, Any]) -> None:
        """Safely save data to JSON file."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logging.error(f"Error saving data: {e}")
            raise

    def load(self) -> Dict[str, Any]:
        """Load data from JSON file with error handling."""
        try:
            if not os.path.exists(self.filepath):
                return {}
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Error loading data: {e}")
            return {}


class UserManager(EventsDatabase):
    def __init__(self, username: str, role: UserRole):
        """Advanced user management with role-based initialization."""
        self.username = username
        self.role = role
        self._security_manager = SecurityManager()
        self._database_manager = self._create_database_manager()
        self._profile = self._initialize_profile()

    def _create_database_manager(self) -> JSONDatabaseManager:
        """Create role-specific database path."""
        base_path = os.path.join(
            "mapp", "database", self.role.name.capitalize(), self.username
        )
        return JSONDatabaseManager(os.path.join(base_path, "user_data.json"))

    def _initialize_profile(self) -> UserProfile:
        """Initialize or load user profile."""
        data = self._database_manager.load()
        return UserProfile(
            username=self.username,
            avatar=data.get("avatar", ""),
            specializations=data.get("specializations", []),
            skills=data.get("skills", []),
        )

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Secure password change mechanism."""
        data = self._database_manager.load()
        if not self._security_manager.verify_password(
            data.get("password", ""), old_password, data.get("salt", "")
        ):
            return False

        salt = os.urandom(16).hex()
        data["password"] = self._security_manager.hash_password(new_password, salt)
        data["salt"] = salt
        self._database_manager.save(data)
        return True

    def update_profile(self, **kwargs) -> None:
        """Flexible profile update method."""
        profile_data = asdict(self._profile)
        profile_data.update(kwargs)
        self._profile = UserProfile(**profile_data)

        data = self._database_manager.load()
        data.update(profile_data)
        self._database_manager.save(data)

    def get_profile(self) -> UserProfile:
        """Get user profile data."""
        return self._profile

    def token_verification(self, token: str) -> bool:
        """Token-based user authentication."""
        data = self._database_manager.load()
        return data.get("token") == token

    @contextmanager
    def transaction(self):
        """Context manager for safe database operations."""
        try:
            yield self
        except Exception as e:
            logging.error(f"Transaction failed: {e}")
            raise


class UserAdvancements:

    def search_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Advanced token-based user search across database."""
        for root, _, files in os.walk("mapp/database"):
            for file in files:
                if file == "user_data.json":
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                            if data.get("token") == token:
                                role = UserRole[
                                    os.path.basename(os.path.dirname(root)).upper()
                                ]
                                return {"role": role, "data": data}
                        except json.JSONDecodeError:
                            logging.warning(f"Invalid JSON in {filepath}")
        return None

    def search_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Advanced username-based user search across database."""
        for root, _, files in os.walk("mapp/database"):
            for file in files:
                if file == "user_data.json":
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                            if data.get("username") == username:
                                role = UserRole[
                                    os.path.basename(os.path.dirname(root)).upper()
                                ]
                                return {"role": role, "data": data}
                        except json.JSONDecodeError:
                            logging.warning(f"Invalid JSON in {filepath}")
        return None

    def create_user(
        self,
        username: str,
        name: str,
        surname: str,
        role: UserRole,
        password: str,
        email: str = None,
        specializations: List[str] = None,
        skills: List[str] = None,
    ):

        user_manager = UserManager(username, role)

        salt = os.urandom(16).hex()

        if role == UserRole.VOLUNTEER:
            spf = {"skills": skills or []}
        else:
            spf = {"specializations": specializations or [], "followers": []}

        user_data = {
            "username": username,
            "name": name,
            "surname": surname,
            "password": user_manager._security_manager.hash_password(password, salt),
            "salt": salt,
            "email": email,
            "avatar": "default_avatar_url",
            "role": role.name,
            "events": [],
            "rating": [],
            "token": f"{role.name[:3]}_{os.urandom(12).hex()}",
            **spf,
        }

        user_manager._database_manager.save(user_data)

        return user_manager

    def follow_user_(
        self,
        follower: str,
        followee: str,
    ):
        follower_manager = UserManager(follower, UserRole.VOLUNTEER)
        followee_manager = UserManager(followee, UserRole.ORGANIZER)

        follower_data = follower_manager._database_manager.load()
        followee_data = followee_manager._database_manager.load()

        if followee not in follower_data.get("following", []):
            follower_data.setdefault("following", []).append(followee)
            follower_manager._database_manager.save(follower_data)

        if follower not in followee_data.get("followers", []):
            followee_data.setdefault("followers", []).append(follower)
            followee_manager._database_manager.save(followee_data)

    def unfollow_user_(
        self,
        follower: str,
        followee: str,
    ):
        follower_manager = UserManager(follower, UserRole.VOLUNTEER)
        followee_manager = UserManager(followee, UserRole.ORGANIZER)

        follower_data = follower_manager._database_manager.load()
        followee_data = followee_manager._database_manager.load()

        if followee in follower_data.get("following", []):
            follower_data["following"].remove(followee)
            follower_manager._database_manager.save(follower_data)

        if follower in followee_data.get("followers", []):
            followee_data["followers"].remove(follower)
            followee_manager._database_manager.save(followee_data)

    def get_followers(
        self,
        username: str,
    ):
        user = self.search_user_by_username(username)

        if user is None:
            return None

        return user["data"].get("followers", [])

    def get_following(
        self,
        username: str,
    ):
        user = self.search_user_by_username(username)

        if user is None:
            return None

        return user["data"].get("following", [])

    def rate_user(
        self,
        who_rate: str,
        who_rated: str,
        rate: float,
        comment: str = None,
    ):

        import random

        who_rated_manager = self.search_user_by_username(who_rated)

        who_rated_data = who_rated_manager["data"]

        _user_mred_ = UserManager(who_rated, UserRole[who_rated_data["role"]])
        _user_mred_data_ = _user_mred_._database_manager.load()

        _user_mred_data_["rating"].append(
            {
                "id_": random.randint(0, 100000),
                "who_rate": who_rate,
                "rate": rate,
                "comment": comment,
            }
        )
        _user_mred_._database_manager.save(_user_mred_data_)

        return who_rated_manager

    def get_avg_rating(
        self,
        username: str,
    ) -> float:
        user = self.search_user_by_username(username)

        if user is None:
            return None

        user_data = user["data"]

        rating = user_data.get("rating", [])

        if not rating:
            return 0
        
        float_rating = [rate["rate"] for rate in rating]

        return sum(float_rating) / len(float_rating)
