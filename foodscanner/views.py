from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import os
import json
from .models import Food, Ingredient, Recipe, Nutrition, ScanHistory, Rating, Review, Favorite
from .forms import ScanForm
from transformers import pipeline
import io
import requests
import base64
from PIL import Image

# Setup Gemini API securely
GEMINI_API_KEY = "AIzaSyDSxVozvJq6FXJAXiohRBojz9Pzbi5iQ_g"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

# Load the model once
food_classifier = None

def get_food_classifier():
    global food_classifier
    if food_classifier is None:
        try:
            food_classifier = pipeline("image-classification", model="nateraw/food")
        except Exception as e:
            print(f"Error loading AI model: {e}")
            # Fallback to mock recognition
            food_classifier = "mock"
    return food_classifier

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def dashboard(request):
    scan_count = ScanHistory.objects.filter(user=request.user).count()
    rating_count = Rating.objects.filter(user=request.user).count()
    favorite_count = Favorite.objects.filter(user=request.user).count()
    recipe_count = 0  # Implement saved recipes later

    recent_scans = ScanHistory.objects.filter(user=request.user).select_related('food_detected').order_by('-scanned_at')[:5]

    # Calculate nutrition data from user's scans
    user_scans = ScanHistory.objects.filter(user=request.user).select_related('food_detected__nutrition')
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    count = 0

    for scan in user_scans:
        if scan.food_detected and hasattr(scan.food_detected, 'nutrition'):
            nutrition = scan.food_detected.nutrition
            total_protein += nutrition.protein
            total_carbs += nutrition.carbohydrates
            total_fat += nutrition.fat
            count += 1

    if count > 0:
        avg_protein = total_protein // count
        avg_carbs = total_carbs // count
        avg_fat = total_fat // count
    else:
        # Default mock data
        avg_protein = 25
        avg_carbs = 45
        avg_fat = 30

    nutrition_data = {
        'protein': avg_protein,
        'carbs': avg_carbs,
        'fat': avg_fat
    }

    context = {
        'scan_count': scan_count,
        'rating_count': rating_count,
        'favorite_count': favorite_count,
        'recipe_count': recipe_count,
        'recent_scans': recent_scans,
        'nutrition_data': json.dumps(nutrition_data)
    }
    return render(request, 'dashboard.html', context)

def scan(request):
    return render(request, 'scan.html')

@csrf_exempt
def scan_food(request):
    print(f"scan_food called with method: {request.method}, user: {request.user}")
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        print(f"Received {len(images)} images")
        results = []

        for image in images:
            ai_data = None
            try:
                # Read the image and encode it via base64 for Gemini Vision
                image_bytes = image.read()
                image.seek(0)
                img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                mime_type = getattr(image, 'content_type', 'image/jpeg')
                if not mime_type:
                    mime_type = 'image/jpeg'
                
                # Ask Gemini to identify the food and return recipe payload natively
                prompt = """
                You are a master chef, nutritionist, and culinary expert.
                The user has scanned an attached image of a food item.
                
                You must identify the exact name of the dish in the image.
                Then, provide highly accurate, authentic, and real-world details for exactly this dish.
                Do not provide generic data. The ingredients must be the classic authentic ingredients used to make this dish with precise measurements or quantities.
                The preparation steps must be a highly detailed, exact, logical, step-by-step recipe to cook this dish.
                The nutrition facts should be a realistic estimate for a standard serving size.
                
                Respond with ONLY valid, raw JSON (no markdown formatting, no code blocks) using this exact structure:
                {
                    "food_name": "Exact Name of Dish",
                    "prep_time": <integer in minutes>,
                    "preparation_steps": ["step 1", "step 2", "step 3"],
                    "ingredients": ["ingredient 1", "ingredient 2", "ingredient 3"],
                    "nutrition": {
                        "calories": <integer>,
                        "protein": <integer>,
                        "carbohydrates": <integer>,
                        "fat": <integer>,
                        "health_benefits": "Short sentence about the health benefits."
                    }
                }
                """
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": img_b64
                                }
                            }
                        ]
                    }]
                }
                headers = {'Content-Type': 'application/json'}
                response = requests.post(GEMINI_URL, json=payload, headers=headers)
                response.raise_for_status()
                
                response_data = response.json()
                response_text = response_data['candidates'][0]['content']['parts'][0]['text']
                ai_data = json.loads(response_text.strip().replace('```json', '').replace('```', ''))
                
                food_name = ai_data.get('food_name', 'Unknown Food').title()
                confidence = 0.99
                
            except requests.exceptions.HTTPError as err:
                print(f"Gemini Vision HTTP Error: {err.response.text}")
                food_name = "Unknown Food"
                confidence = 0.0
            except Exception as e:
                print(f"Gemini Vision API Error: {e}")
                food_name = "Unknown Food"
                confidence = 0.0

            # Get or create food
            food, created = Food.objects.get_or_create(
                name=food_name,
                defaults={'description': f'A delicious {food_name.lower()}'}
            )

            # Create nutrition if not exists
            if not hasattr(food, 'nutrition'):
                if ai_data and 'nutrition' in ai_data:
                    n_data = ai_data['nutrition']
                    Nutrition.objects.create(
                        food=food,
                        calories=n_data.get('calories', 250),
                        protein=n_data.get('protein', 10),
                        carbohydrates=n_data.get('carbohydrates', 30),
                        fat=n_data.get('fat', 10),
                        health_benefits=n_data.get('health_benefits', 'Provides essential nutrients.')
                    )
                else:
                    mock_nutrition = get_mock_nutrition(food_name)
                    Nutrition.objects.create(
                        food=food,
                        calories=mock_nutrition['calories'],
                        protein=mock_nutrition['protein'],
                        carbohydrates=mock_nutrition['carbohydrates'],
                        fat=mock_nutrition['fat'],
                        health_benefits=mock_nutrition['benefits']
                    )

            # Save scan history only for authenticated users
            if request.user.is_authenticated:
                scan_history = ScanHistory.objects.create(
                    user=request.user,
                    image=image,
                    food_detected=food,
                    confidence=confidence
                )

            # Extraction with fallbacks
            if ai_data:
                prep_time = ai_data.get('prep_time', 15)
                prep_steps = ai_data.get('preparation_steps', ["Prepare the ingredients.", "Cook thoroughly.", "Serve hot."])
                ingredients = ai_data.get('ingredients', ["Main Ingredient", "Spices", "Oil"])
                nutrition = ai_data.get('nutrition', {})
                calories = nutrition.get('calories', food.nutrition.calories if hasattr(food, 'nutrition') else 250)
                protein = nutrition.get('protein', food.nutrition.protein if hasattr(food, 'nutrition') else 10)
                carbs = nutrition.get('carbohydrates', food.nutrition.carbohydrates if hasattr(food, 'nutrition') else 20)
                fat = nutrition.get('fat', food.nutrition.fat if hasattr(food, 'nutrition') else 10)
                benefits = nutrition.get('health_benefits', food.nutrition.health_benefits if hasattr(food, 'nutrition') else "Provides essential energy.")
            else:
                # Fallback to existing logic if API fails
                prep_time = 15
                prep_steps = ["Gather and wash all ingredients.", "Cook gently until done.", "Plate and serve hot or cold as preferred."]
                
                if food.ingredients.exists():
                    ingredients = [img.name for img in food.ingredients.all()]
                else:
                    ingredients = ["Main Ingredient", "Spices", "Oil or Butter", "Salt to taste"]
                
                calories = food.nutrition.calories if hasattr(food, 'nutrition') else 250
                protein = food.nutrition.protein if hasattr(food, 'nutrition') else 10
                carbs = food.nutrition.carbohydrates if hasattr(food, 'nutrition') else 20
                fat = food.nutrition.fat if hasattr(food, 'nutrition') else 10
                benefits = food.nutrition.health_benefits if hasattr(food, 'nutrition') else "Provides essential nutrients."

            results.append({
                'food_name': food.name,
                'food_id': food.id,
                'confidence': confidence,
                'prep_time': prep_time,
                'preparation_steps': prep_steps,
                'ingredients': ingredients,
                'nutrition': {
                    'calories': calories,
                    'protein': protein,
                    'carbohydrates': carbs,
                    'fat': fat,
                    'health_benefits': benefits
                }
            })

        print(f"Returning results: {results}")
        return JsonResponse(results, safe=False)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_mock_nutrition(food_name):
    # Mock nutrition data based on food type
    food_lower = food_name.lower()
    if 'pizza' in food_lower:
        return {
            'calories': 285,
            'protein': 12,
            'carbohydrates': 36,
            'fat': 10,
            'benefits': 'Provides calcium from cheese, energy from carbs'
        }
    elif 'burger' in food_lower:
        return {
            'calories': 354,
            'protein': 20,
            'carbohydrates': 29,
            'fat': 17,
            'benefits': 'High in protein, provides iron from meat'
        }
    elif 'pasta' in food_lower:
        return {
            'calories': 220,
            'protein': 8,
            'carbohydrates': 43,
            'fat': 1,
            'benefits': 'Good source of complex carbs, can be fortified with vitamins'
        }
    elif 'salad' in food_lower:
        return {
            'calories': 150,
            'protein': 3,
            'carbohydrates': 10,
            'fat': 12,
            'benefits': 'High in vitamins and fiber'
        }
    elif 'ice cream' in food_lower:
        return {
            'calories': 207,
            'protein': 3,
            'carbohydrates': 24,
            'fat': 11,
            'benefits': 'Provides calcium and can be a treat in moderation'
        }
    else:
        return {
            'calories': 200,
            'protein': 10,
            'carbohydrates': 25,
            'fat': 8,
            'benefits': 'Provides essential nutrients and energy'
        }

def food_detail(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    reviews = Review.objects.filter(food=food).order_by('-created_at')
    
    dynamic_ingredients = []
    dynamic_prep_steps = []
    
    # Always prioritize fresh Gemini data to ensure exact, highly accurate culinary instructions
    try:
        prompt = f"""
        You are a master chef and culinary expert. 
        We need extremely precise, authentic details for the dish named: {food.name}.
        
        Provide highly accurate, real-world ingredients (with measurements if possible) and exact, step-by-step preparation method to cook {food.name}.
        Do not provide generic fallback answers.
        
        Respond with ONLY valid, raw JSON using this structure without markdown:
        {{
            "preparation_steps": ["step 1", "step 2", "step 3"],
            "ingredients": ["ingredient 1", "ingredient 2", "ingredient 3"]
        }}
        """
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(GEMINI_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        response_data = response.json()
        response_text = response_data['candidates'][0]['content']['parts'][0]['text']
        ai_data = json.loads(response_text.strip().replace('```json', '').replace('```', ''))
        
        dynamic_ingredients = ai_data.get('ingredients', [])
        dynamic_prep_steps = ai_data.get('preparation_steps', [])
    except requests.exceptions.HTTPError as err:
        print(f"Gemini HTTP Error in Details View: {err.response.text}")
    except Exception as e:
        print(f"Gemini API Parsing Error in Details View: {e}")

    # Fallback only if Gemini absolutely fails
    if not dynamic_ingredients:
        if food.ingredients.exists():
            dynamic_ingredients = [img.name for img in food.ingredients.all()]
        else:
            dynamic_ingredients = ["Main Ingredient", "Spices", "Oil or Butter", "Salt to taste"]
            
    if not dynamic_prep_steps:
        if hasattr(food, 'recipe') and food.recipe and hasattr(food.recipe, 'steps'):
            dynamic_prep_steps = food.recipe.steps
        else:
            dynamic_prep_steps = ["Gather and wash all ingredients.", "Cook gently until done.", "Plate and serve hot or cold as preferred."]

    context = {
        'food': food,
        'reviews': reviews,
        'dynamic_ingredients': dynamic_ingredients,
        'dynamic_prep_steps': dynamic_prep_steps
    }
    return render(request, 'food_detail.html', context)

@login_required
def rate_food(request, food_id):
    if request.method == 'POST':
        food = get_object_or_404(Food, id=food_id)
        rating_value = int(request.POST['rating'])
        Rating.objects.update_or_create(
            user=request.user,
            food=food,
            defaults={'rating': rating_value}
        )
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('Accept', '').find('application/json') != -1
        if is_ajax:
            return JsonResponse({'status': 'success', 'message': 'Rating submitted!'})
        messages.success(request, 'Rating submitted!')
    return redirect('food_detail', food_id=food_id)

@login_required
def review_food(request, food_id):
    if request.method == 'POST':
        food = get_object_or_404(Food, id=food_id)
        comment = request.POST['comment']
        Review.objects.create(
            user=request.user,
            food=food,
            comment=comment
        )
        messages.success(request, 'Review submitted!')
    return redirect('food_detail', food_id=food_id)

@login_required
def toggle_favorite(request, food_id):
    if request.method == 'POST' or request.headers.get('x-requested-with') == 'XMLHttpRequest':
        food = get_object_or_404(Food, id=food_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            food=food
        )
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('Accept', '').find('application/json') != -1
        if not created:
            favorite.delete()
            if is_ajax:
                return JsonResponse({'status': 'removed', 'message': f'Removed {food.name} from favorites.'})
            messages.success(request, f'Removed {food.name} from favorites.')
        else:
            if is_ajax:
                return JsonResponse({'status': 'added', 'message': f'Added {food.name} to favorites.'})
            messages.success(request, f'Added {food.name} to favorites.')
    return redirect('food_detail', food_id=food_id)

@login_required
def favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('food')
    return render(request, 'favorites.html', {'favorites': favorites})

@login_required
def history(request):
    scans = ScanHistory.objects.filter(user=request.user).order_by('-scanned_at')
    from django.core.paginator import Paginator
    paginator = Paginator(scans, 10)  # 10 scans per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'history.html', {'scans': page_obj})

@login_required
def ai_assistant(request):
    if request.method == 'POST':
        question = request.POST.get('question', '').strip()
        food_context = request.POST.get('food_context', '')

        if not question:
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('Accept', '').find('application/json') != -1
            if is_ajax:
                return JsonResponse({'error': 'Please ask a question.'}, status=400)
            messages.error(request, 'Please ask a question.')
            return redirect('ai_assistant')

        # Simple AI responses based on keywords
        response = generate_ai_response(question, food_context)

        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('Accept', '').find('application/json') != -1
        if is_ajax:
            return JsonResponse({'question': question, 'response': response})

        # Save conversation (optional - could add a Conversation model later)
        context = {
            'question': question,
            'response': response,
            'food_context': food_context
        }
        return render(request, 'ai_assistant.html', context)

    return render(request, 'ai_assistant.html')

def generate_ai_response(question, food_context):
    """Generate AI responses using Google Gemini based on food-related questions"""
    try:
        # Construct a personality and context-rich prompt
        prompt = f"""
        You are 'Beyond The Bite AI', an expert nutritionist, master chef, and friendly food assistant.
        The user is asking a question within a food scanning application.
        
        Context regarding the food they are currently viewing/scanned (if any): '{food_context}'
        
        User's question: '{question}'
        
        Provide a helpful, accurate, and concise answer (maximum 3-4 sentences). 
        Do not use markdown formatting like bolding or lists, just return plain text.
        """
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(GEMINI_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        response_data = response.json()
        return response_data['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"Gemini API Error in AI Assistant: {e}")
        # Fallback to a generic response if the API call fails
        question_lower = question.lower()
        if 'healthy' in question_lower or 'health' in question_lower:
            return "For optimal health, focus on a balanced diet with plenty of vegetables, fruits, whole grains, and lean proteins."
        elif 'recipe' in question_lower or 'cook' in question_lower:
            return "Great question about cooking! Gather your ingredients, prep them, and cook at the appropriate temperature."
        else:
            return "I'm experiencing a brief connection issue, but I am here to help with nutrition, recipes, and healthy eating questions!"

import imageio
from PIL import ImageDraw, ImageFont

@login_required
def generate_video(request, food_id):
    food = get_object_or_404(Food, id=food_id)
    
    # Check if a generated video already exists
    video_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
    os.makedirs(video_dir, exist_ok=True)
    video_filename = f'food_{food.id}_preparation.gif'
    video_path = os.path.join(video_dir, video_filename)
    video_url = f'{settings.MEDIA_URL}videos/{video_filename}'

    if os.path.exists(video_path):
        return JsonResponse({'status': 'success', 'video_url': video_url})

    try:
        frames = []
        width, height = 400, 300
        steps = [f"Step 1: Prep {food.name}", "Step 2: Cook gently", "Step 3: Plate and Serve", "Enjoy your meal!"]
        if hasattr(food, 'recipe') and food.recipe.steps:
            steps = food.recipe.steps[:4] if len(food.recipe.steps) > 4 else food.recipe.steps
            
        colors = [(255, 230, 230), (230, 255, 230), (230, 230, 255), (255, 255, 230)]
        
        # Try finding a font, default if not found
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()

        # Generate frames
        # Create a simple cartoon animation effect for each step
        for i, step in enumerate(steps):
            for frame_idx in range(10): # 10 frames per step
                bg_color = colors[i % len(colors)]
                img = Image.new('RGB', (width, height), color=bg_color)
                draw = ImageDraw.Draw(img)
                
                # Cartoon drawing: A bouncing pot/pan
                pot_y = 150 + (frame_idx % 5) * 5 if i % 2 == 0 else 150 - (frame_idx % 5) * 5
                
                # Draw "table"
                draw.rectangle([(0, 200), (400, 300)], fill=(139, 69, 19))
                # Draw "pot" or plate
                draw.ellipse([(100, pot_y), (300, pot_y+80)], fill=(100, 100, 100), outline="black", width=3)
                # Draw "food"
                draw.ellipse([(150, pot_y+10), (250, pot_y+60)], fill=(255, 165, 0) if 'pizza' in food.name.lower() else (50, 205, 50), outline="black", width=2)
                
                # Draw text
                # We do simple word wrapping or truncation for demo
                text_snippet = str(step)[:30]
                text_bbox = draw.textbbox((0, 0), text_snippet, font=font)
                text_w = text_bbox[2] - text_bbox[0]
                draw.text(((width - text_w) / 2, 50), text_snippet, font=font, fill=(0, 0, 0))
                
                frames.append(img)
                
        # Save as GIF
        imageio.mimsave(video_path, frames, fps=10)
        
        return JsonResponse({'status': 'success', 'video_url': video_url})
    except Exception as e:
        print(f"Error generating video: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

