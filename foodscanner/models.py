from django.db import models
from django.contrib.auth.models import User

class Food(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='food_images/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    food = models.ManyToManyField(Food, related_name='ingredients')

    def __str__(self):
        return self.name

class Recipe(models.Model):
    food = models.OneToOneField(Food, on_delete=models.CASCADE, related_name='recipe')
    steps = models.JSONField(default=list, help_text='List of preparation steps')  # Store as JSON array
    video_url = models.URLField(blank=True)
    preparation_time = models.IntegerField(help_text='in minutes')
    cooking_time = models.IntegerField(default=0, help_text='in minutes')
    servings = models.IntegerField(default=1)

    def __str__(self):
        return f"Recipe for {self.food.name}"

class Nutrition(models.Model):
    food = models.OneToOneField(Food, on_delete=models.CASCADE, related_name='nutrition')
    calories = models.FloatField()
    protein = models.FloatField()  # in grams
    carbohydrates = models.FloatField()
    fat = models.FloatField()
    health_benefits = models.TextField(blank=True)

    def __str__(self):
        return f"Nutrition for {self.food.name}"

class ScanHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='scanned_images/')
    food_detected = models.ForeignKey(Food, on_delete=models.SET_NULL, null=True)
    confidence = models.FloatField(default=0.0)
    scanned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan by {self.user.username} at {self.scanned_at}"

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'food')

    def __str__(self):
        return f"{self.user.username} rated {self.food.name} {self.rating} stars"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.food.name}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'food')

    def __str__(self):
        return f"{self.user.username} favorited {self.food.name}"
