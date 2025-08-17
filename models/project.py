class Project:
    def __init__(self, title, description, platform, url, budget, date_posted=None, deadline=None):
        self.title = title
        self.description = description
        self.platform = platform
        self.url = url
        self.budget = budget
        self.date_posted = date_posted
        self.deadline = deadline

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "platform": self.platform,
            "url": self.url,
            "budget": self.budget,
            "datePosted": self.date_posted,
            "deadline": self.deadline
        }

    def __repr__(self):
        return (
            f"{self.title} ({self.platform})\n"
            f"{self.description}\n"
            f"Budget : {self.budget}\n"
            f"Publié le : {self.date_posted} | Expire le : {self.deadline}\n"
            f"{self.url}\n"
        )
