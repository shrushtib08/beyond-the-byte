from django.contrib import admin
from .models import Food, Ingredient, Recipe, Nutrition, ScanHistory, Rating, Review, Favorite

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'get_rating_count', 'get_favorites_count')
    search_fields = ('name', 'description')
    list_per_page = 20

    def get_rating_count(self, obj):
        return Rating.objects.filter(food=obj).count()
    get_rating_count.short_description = 'Ratings'

    def get_favorites_count(self, obj):
        return Favorite.objects.filter(food=obj).count()
    get_favorites_count.short_description = 'Favorites'

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_food_count')
    search_fields = ('name',)

    def get_food_count(self, obj):
        return obj.food_set.count()
    get_food_count.short_description = 'Used in Foods'

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('food', 'preparation_time', 'cooking_time', 'servings')
    search_fields = ('food__name',)
    readonly_fields = ('food',)

@admin.register(Nutrition)
class NutritionAdmin(admin.ModelAdmin):
    list_display = ('food', 'calories', 'protein', 'carbohydrates', 'fat')
    search_fields = ('food__name',)
    readonly_fields = ('food',)

@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_detected', 'scanned_at', 'confidence')
    list_filter = ('scanned_at', 'food_detected')
    search_fields = ('user__username', 'food_detected__name')
    readonly_fields = ('user', 'food_detected', 'scanned_at', 'image', 'confidence')
    date_hierarchy = 'scanned_at'
    list_per_page = 50

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'food', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'food__name')
    date_hierarchy = 'created_at'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'food', 'created_at', 'get_comment_preview')
    search_fields = ('user__username', 'food__name', 'comment')
    date_hierarchy = 'created_at'
    list_per_page = 50

    def get_comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    get_comment_preview.short_description = 'Comment'

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'food', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'food__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'food', 'created_at')
