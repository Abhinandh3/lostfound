from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ('USER', 'User'),
        ('DETECTIVE', 'Detective'),
        ('ADMIN', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    district = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    is_detective = models.BooleanField(default=False)
    detective_verified = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    cases_posted = models.PositiveIntegerField(default=0)
    cases_solved = models.PositiveIntegerField(default=0)
    total_reward_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Case(models.Model):
    CASE_TYPES = [
        ("LOST", "Lost"),
        ("FOUND", "Found"),
    ]

    CATEGORY = [
        ("PERSON", "Person"),
        ("PET", "Pet"),
    ]

    STATUS = [
        ("OPEN", "Open"),
        ("UNDER_INVESTIGATION", "Under Investigation"),
        ("MATCH_FOUND", "Match Found"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    ]

    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='cases')
    case_type = models.CharField(max_length=10, choices=CASE_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORY)
    title = models.CharField(max_length=200)
    description = models.TextField()
    last_seen_location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    date = models.DateField()
    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True)
    status = models.CharField(max_length=30, choices=STATUS, default='OPEN')
    contact_phone = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.case_type} - {self.title}"


class CaseImage(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="cases/")
    is_primary = models.BooleanField(default=False)
    clip_embedding = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.case.title}"


class SightingReport(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='sightings')
    reporter = models.ForeignKey(Profile, on_delete=models.CASCADE)
    description = models.TextField()
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to="sightings/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sighting for {self.case.title}"


class DetectiveApplication(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    experience_years = models.IntegerField(default=0)
    photo = models.ImageField(upload_to="detectives/")
    govt_id = models.FileField(upload_to="documents/")
    address_proof = models.FileField(upload_to="documents/")
    certificates = models.FileField(upload_to="documents/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} - Detective Application"


class DetectiveRequest(models.Model):
    STATUS = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='detective_request')
    requested_by = models.ForeignKey(Profile, on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request for {self.case.title}"


class CaseAssignment(models.Model):
    STATUS = [
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='assignments')
    detective = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_cases')
    status = models.CharField(max_length=20, choices=STATUS, default='ACTIVE')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.case.title} assigned to {self.detective.user.username}"


class InvestigationUpdate(models.Model):
    MILESTONE_CHOICES = [
        ('STARTED', 'Investigation Started'),
        ('LOCATION_VISITED', 'Location Visited'),
        ('WITNESS_FOUND', 'Witness Found'),
        ('EVIDENCE_ADDED', 'Evidence Added'),
        ('MATCH_FOUND', 'Match Found'),
        ('CLOSED', 'Case Closed'),
    ]

    assignment = models.ForeignKey(CaseAssignment, on_delete=models.CASCADE, related_name='updates')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="updates/", blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    milestone = models.CharField(max_length=30, choices=MILESTONE_CHOICES, default='STARTED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update for {self.assignment.case.title}"


class DetectiveAchievement(models.Model):
    detective = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="achievements/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.detective.user.username} - {self.title}"


class Feedback(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    admin_reply = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.user.username}"


class Blog(models.Model):
    CATEGORY_CHOICES = [
        ('SAFETY', 'Safety Tips'),
        ('SUCCESS_STORY', 'Success Story'),
        ('PET_CARE', 'Pet Care'),
        ('MISSING_ALERT', 'Missing Alert'),
    ]

    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='SAFETY')
    cover_image = models.ImageField(upload_to="blog/")
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    recipient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.recipient.user.username}"
