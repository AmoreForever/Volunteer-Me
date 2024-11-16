import os
import json

from misc import utils
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from lightdb import LightDB

PAPPER = "thispaperistoolongthatnoonecancrackitgoodluck)"


def generate_salt() -> str:
    """Generate a random salt."""
    return os.urandom(16).hex()


class AdvancedPasswordHasher(PasswordHasher):
    def __init__(self):
        """Initialize the password hasher with specific parameters."""
        super().__init__(
            time_cost=4,
            memory_cost=102400,
            parallelism=8,
            hash_len=60,
            salt_len=32,
            encoding="utf-8",
        )

    def hash_password(self, password: str, salt: str) -> str:
        """Hash the password with salt and additional pepper."""
        return self.hash(password + salt + PAPPER)

    def verify_password(self, password: str, salt: str, hashed: str) -> bool:
        """Verify the hashed password."""
        try:
            self.verify(hashed, password + salt + PAPPER)
            return True
        except argon2_exceptions.VerifyMismatchError:
            return False
        except TypeError:
            return False


class Applications:
    def __init__(self) -> None:
        """Initialize the applications database."""
        self.filepath = os.path.join("workify", "database", "applications.json")
        self._load_data()

    def _load_data(self):
        """Load application data from JSON file."""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as file:
                self.data = json.load(file)
        else:
            self.data = {"applications": []}

    def _save_data(self):
        """Save application data to JSON file."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)

    def get_applications_available(self) -> list:
        """Get all available applications."""
        return self.data.get("applications", [])

    def create_application(self, application: dict) -> None:
        """Create a new application."""
        self.data["applications"].append(application)
        self._save_data()

    def get_applications(self) -> list:
        """Get all applications."""
        return self.data.get("applications", [])

    def get_application(self, application_id: str) -> dict:
        """Get a specific application by ID."""
        return next(
            (app for app in self.data["applications"] if app["id"] == application_id),
            None,
        )

    def update_application(self, application_id: str, application: dict) -> None:
        """Update an existing application by ID."""
        for i, app in enumerate(self.data["applications"]):
            if app["id"] == application_id:
                self.data["applications"][i] = application
                self._save_data()
                break

    def assign_volunteer(self, application_id: str, volunteer: str) -> None:
        """Assign a volunteer to an application."""
        if application := self.get_application(application_id):
            if volunteer not in application["volunteers"]:
                application["volunteers"].append(volunteer)
                self.update_application(application_id, application)
                return True
            return False

    def update_status(self, application_id: str, status: str) -> None:
        """Update the status of an application."""
        self._update_field(application_id, "status", status)

    def _update_field(self, application_id: str, field: str, value) -> None:
        """Generic method to update a field in a specific application."""
        if application := self.get_application(application_id):
            application[field] = value
            self.update_application(application_id, application)

    def _get_last_id(self) -> int:
        """Get the last application ID."""
        return max((int(app["id"]) for app in self.data["applications"]), default=0)

    def get_applications(self) -> list:
        """Get all applications."""
        return self.data.get("applications", [])

    def get_volunteers(self, application_id: str) -> list:
        """Get all volunteers for an application."""
        return self.get_application(application_id).get("volunteers", [])

    def get_my_applications(self, username: str) -> list:
        """Get all applications for a specific user."""
        applications = self.get_applications()

        return [app for app in applications if app.get("who_created") == username]


class VolunteerDatabase(LightDB, Applications):
    def __init__(self, username: str) -> None:
        """Initialize the user database."""
        self.filepath = os.path.join(
            "workify", "database", "volunteer", username, "data.json"
        )
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.username = username
        self.password_hasher = AdvancedPasswordHasher()
        self.salt = generate_salt()
        super().__init__(self.filepath)

    def create_user(self, password: str) -> None:
        """Create a new user entry with hashed password and metadata."""
        self.set("password", self.password_hasher.hash_password(password, self.salt))
        self.set("salt", self.salt)

        self.set(
            "avatar",
            "https://i.pinimg.com/564x/8e/cd/1a/8ecd1a5afdbd3ec270aa868c235c7d80.jpg",
        )
        self.set("is_available", True)
        self.set("username", self.username)
        self.save()

    def verify_user_by_token(self, token: str) -> bool:
        """Verify the user token."""
        return self.get("token") == token

    def verify_user(self, password: str) -> bool:
        """Verify the user password."""
        hashed = self.get("password")
        return self.password_hasher.verify_password(password, self.get("salt"), hashed)

    def get_token(self):
        return self.get("token")

    def get_user(self):
        return self.get("username")

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change the user password."""
        if not self.verify_user(old_password):
            return False
        self.set(
            "password",
            self.password_hasher.hash_password(new_password, self.get("salt")),
        )
        self.save()
        return True

    def change_avatar(self, avatar: str) -> None:
        """Change the user avatar."""
        self.set("avatar", avatar)
        self.save()

    def get_avatar(self) -> str:
        """Get the user avatar."""
        return self.get("avatar")

    def get_username(self) -> str:
        """Get the username."""
        return self.get("username")

    def get_data(self) -> dict:
        """Get the user data."""
        return {
            "username": self.get_username(),
            "avatar": self.get_avatar(),
        }

    def specializations(self, specializations: list) -> None:
        """Set the user specializations."""
        self.set("specializations", specializations)
        self.save()

    def get_specializations(self) -> list:
        """Get the user specializations."""
        return self.get("specializations")

    def add_specialization(self, specialization: str) -> None:
        """Add a new specialization."""
        specializations = self.get_specializations()
        specializations.append(specialization)
        self.specializations(specializations)

    def remove_specialization(self, specialization: str) -> None:
        """Remove a specialization."""
        specializations = self.get_specializations()
        specializations.remove(specialization)
        self.specializations(specializations)

    def add_experience(self, experience: dict) -> None:
        """Add a new experience."""
        experiences = self.get("experiences", [])
        experiences.append(experience)
        self.set("experiences", experiences)
        self.save()

    def get_experiences(self) -> list:
        """Get the user experiences."""
        return self.get("experiences", [])

    def add_education(self, education: dict) -> None:
        """Add a new education."""
        educations = self.get("educations", [])
        educations.append(education)
        self.set("educations", educations)
        self.save()

    def get_educations(self) -> list:
        """Get the user educations."""
        return self.get("educations", [])

    def add_feedback(self, feedback: dict) -> None:
        """Add a new feedback."""
        feedbacks = self.get("feedbacks", [])
        feedbacks.append(feedback)
        self.set("feedbacks", feedbacks)
        self.save()

    def set_skills(self, skills: list) -> None:
        """Set the user skills."""
        self.set("skills", skills)
        self.save()

    def get_skills(self) -> list:
        """Get the user skills."""
        return self.get("skills", [])

    def update_token(self) -> None:
        """Update the user token."""

        self.set("token", utils.generate_token("vol_"))
        self.save()


class OrganizerDatabase(LightDB, Applications):
    def __init__(self, username: str) -> None:
        """Initialize the user database."""
        self.filepath = os.path.join(
            "workify", "database", "Organizer", username, "data.json"
        )
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self.username = username
        self.password_hasher = AdvancedPasswordHasher()
        self.salt = generate_salt()
        super().__init__(self.filepath)

    def create_user(self, password: str) -> None:
        """Create a new user entry with hashed password and metadata."""
        self.set("password", self.password_hasher.hash_password(password, self.salt))
        self.set("salt", self.salt)

        self.set(
            "avatar",
            "https://i.pinimg.com/564x/26/50/bc/2650bc1bd16136e83b9b289632a04575.jpg",
        )
        self.set("is_available", True)
        self.set("username", self.username)
        self.save()

    def update_token(self) -> None:
        """Update the user token."""

        self.set("token", utils.generate_token("org_"))
        self.save()

    def verify_user(self, password: str) -> bool:
        """Verify the user password."""
        hashed = self.get("password")
        return self.password_hasher.verify_password(password, self.get("salt"), hashed)

    def get_user(self):
        return self.get("username")

    def get_token(self):
        return self.get("token")

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change the user password."""
        if not self.verify_user(old_password):
            return False
        self.set(
            "password",
            self.password_hasher.hash_password(new_password, self.get("salt")),
        )
        self.save()
        return True

    def change_avatar(self, avatar: str) -> None:
        """Change the user avatar."""
        self.set("avatar", avatar)
        self.save()

    def get_avatar(self) -> str:
        """Get the user avatar."""
        return self.get("avatar")

    def get_username(self) -> str:
        """Get the username."""
        return self.get("username")

    def get_data(self) -> dict:
        """Get the user data."""
        return {
            "username": self.get_username(),
            "avatar": self.get_avatar(),
        }

    def create_application(self, application: dict) -> None:
        """Create a new application."""
        applications = self.get("applications", [])
        applications.append(application)
        self.set("applications", applications)
        self.save()

    def get_applications(self) -> list:
        """Get the user applications."""
        return self.get("applications", [])


def search_user_by_token(token):
    """Search user by token. and give role and data, without LightDB"""

    for root, dirs, files in os.walk("workify/database"):
        for file in files:
            if file == "data.json":
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("token") == token:
                        return {"role": root.split("\\")[1], "data": data}


# organizer = OrganizerDatabase("Fazliddin")
# organizer.create_user("Fazliddin123")

# volunteer = VolunteerDatabase("Aziz")
# volunteer.create_user("Aziz123")

# # print(search_user_by_token("vol_8ad5e3accae79ec6"))

    # app = Applications()
    # print(app.get_my_applications("Fazliddin"))
