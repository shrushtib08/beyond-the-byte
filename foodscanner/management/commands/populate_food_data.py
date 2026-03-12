from django.core.management.base import BaseCommand
from foodscanner.models import Food, Ingredient, Recipe, Nutrition

class Command(BaseCommand):
    help = 'Populate database with sample food data'

    def handle(self, *args, **options):
        self.stdout.write('Populating sample food data...')

        # Sample food data
        foods_data = [
            {
                'name': 'Pizza',
                'description': 'A delicious Italian dish with tomato sauce, cheese, and various toppings',
                'ingredients': ['Dough', 'Tomato Sauce', 'Mozzarella Cheese', 'Pepperoni', 'Olive Oil'],
                'nutrition': {
                    'calories': 285,
                    'protein': 12,
                    'carbohydrates': 36,
                    'fat': 10,
                    'benefits': 'Provides calcium from cheese, energy from carbs, protein from toppings'
                },
                'recipe': {
                    'steps': [
                        'Preheat oven to 475°F (245°C)',
                        'Roll out pizza dough on a floured surface',
                        'Spread tomato sauce evenly over the dough',
                        'Add mozzarella cheese and toppings',
                        'Drizzle with olive oil and season',
                        'Bake for 12-15 minutes until crust is golden'
                    ],
                    'video_url': 'https://www.youtube.com/watch?v=example',
                    'preparation_time': 20,
                    'cooking_time': 15,
                    'servings': 4
                }
            },
            {
                'name': 'Burger',
                'description': 'A classic American sandwich with beef patty, lettuce, tomato, and special sauce',
                'ingredients': ['Beef Patty', 'Burger Bun', 'Lettuce', 'Tomato', 'Cheese', 'Special Sauce'],
                'nutrition': {
                    'calories': 354,
                    'protein': 20,
                    'carbohydrates': 29,
                    'fat': 17,
                    'benefits': 'High in protein, provides iron from meat, calcium from cheese'
                },
                'recipe': {
                    'steps': [
                        'Form ground beef into patties and season with salt and pepper',
                        'Heat grill or skillet over medium-high heat',
                        'Cook patties for 4-5 minutes per side until desired doneness',
                        'Toast burger buns lightly',
                        'Assemble with lettuce, tomato, cheese, and sauce',
                        'Serve immediately'
                    ],
                    'video_url': 'https://www.youtube.com/watch?v=example',
                    'preparation_time': 10,
                    'cooking_time': 10,
                    'servings': 1
                }
            },
            {
                'name': 'Pasta',
                'description': 'Italian pasta dish with tomato sauce and herbs',
                'ingredients': ['Pasta', 'Tomato Sauce', 'Garlic', 'Olive Oil', 'Basil', 'Parmesan Cheese'],
                'nutrition': {
                    'calories': 220,
                    'protein': 8,
                    'carbohydrates': 43,
                    'fat': 1,
                    'benefits': 'Good source of complex carbs, can be fortified with vitamins'
                },
                'recipe': {
                    'steps': [
                        'Boil pasta in salted water according to package directions',
                        'Heat olive oil in a pan and sauté minced garlic',
                        'Add tomato sauce and simmer for 5 minutes',
                        'Drain pasta and add to sauce',
                        'Toss with fresh basil and parmesan cheese',
                        'Serve hot'
                    ],
                    'video_url': 'https://www.youtube.com/watch?v=example',
                    'preparation_time': 5,
                    'cooking_time': 15,
                    'servings': 4
                }
            },
            {
                'name': 'Salad',
                'description': 'Fresh mixed greens with vegetables and light dressing',
                'ingredients': ['Mixed Greens', 'Cherry Tomatoes', 'Cucumber', 'Carrots', 'Olive Oil', 'Balsamic Vinegar'],
                'nutrition': {
                    'calories': 150,
                    'protein': 3,
                    'carbohydrates': 10,
                    'fat': 12,
                    'benefits': 'High in vitamins and fiber, low in calories'
                },
                'recipe': {
                    'steps': [
                        'Wash and dry all vegetables thoroughly',
                        'Chop cucumber and carrots into bite-sized pieces',
                        'Toss mixed greens with tomatoes and chopped vegetables',
                        'Mix olive oil and balsamic vinegar for dressing',
                        'Drizzle dressing over salad and toss gently',
                        'Serve fresh'
                    ],
                    'video_url': 'https://www.youtube.com/watch?v=example',
                    'preparation_time': 15,
                    'cooking_time': 0,
                    'servings': 2
                }
            }
        ]

        for food_data in foods_data:
            # Create or get food
            food, created = Food.objects.get_or_create(
                name=food_data['name'],
                defaults={'description': food_data['description']}
            )

            if created:
                self.stdout.write(f'Created food: {food.name}')

                # Add ingredients
                for ingredient_name in food_data['ingredients']:
                    ingredient, _ = Ingredient.objects.get_or_create(name=ingredient_name)
                    food.ingredients.add(ingredient)

                # Add nutrition
                Nutrition.objects.create(
                    food=food,
                    calories=food_data['nutrition']['calories'],
                    protein=food_data['nutrition']['protein'],
                    carbohydrates=food_data['nutrition']['carbohydrates'],
                    fat=food_data['nutrition']['fat'],
                    health_benefits=food_data['nutrition']['benefits']
                )

                # Add recipe
                Recipe.objects.create(
                    food=food,
                    **food_data['recipe']
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated sample food data'))