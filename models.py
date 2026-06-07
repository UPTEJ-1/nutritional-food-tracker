"""
AS91906 Complex Programming Standard - Object-Oriented Models

This module demonstrates proficiency in object-oriented programming by defining
two main classes: FoodEntry and NutritionCalculator. These classes encapsulate
nutrition tracking logic using:
- Multiple classes with distinct responsibilities
- Instance attributes and methods
- Complex logic including calculations and data aggregation
- Proper documentation and code organization
"""


class FoodEntry:
    """
    Represents a single food entry logged by a user.

    This class encapsulates all data related to a logged food item, including
    its nutritional information and context (meal type, quantity). It provides
    methods to retrieve data in various formats for display and analysis.

    Attributes:
        food_id (int): Unique identifier for the food in the database
        food_name (str): Name of the food item
        quantity_grams (float): Quantity of food consumed in grams
        meal_type (str): Type of meal (e.g., "Breakfast", "Lunch", "Snack")
        calories (float): Total calories for this entry
        protein (float): Total protein in grams for this entry
        carbs (float): Total carbohydrates in grams for this entry
        fats (float): Total fats in grams for this entry
    """

    def __init__(self, food_id, food_name, quantity_grams, meal_type, calories, protein, carbs, fats):
        """
        Initializes a FoodEntry object with nutritional data.

        Args:
            food_id (int): Unique identifier for the food
            food_name (str): Name of the food
            quantity_grams (float): Quantity in grams
            meal_type (str): Type of meal
            calories (float): Total calories
            protein (float): Total protein in grams
            carbs (float): Total carbohydrates in grams
            fats (float): Total fats in grams
        """
        self.food_id = food_id
        self.food_name = food_name
        self.quantity_grams = quantity_grams
        self.meal_type = meal_type
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fats = fats

    def get_summary(self):
        """
        Returns a formatted summary string of the food entry.

        Returns:
            str: Formatted string like "150g Chicken Breast - 248 kcal"
        """
        return f"{self.quantity_grams}g {self.food_name} - {self.calories:.0f} kcal"

    def to_dict(self):
        """
        Converts the FoodEntry object to a dictionary.

        Returns:
            dict: Dictionary containing all attributes of the food entry
        """
        return {
            'food_id': self.food_id,
            'food_name': self.food_name,
            'quantity_grams': self.quantity_grams,
            'meal_type': self.meal_type,
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fats': self.fats
        }


class NutritionCalculator:
    """
    Calculates and analyzes nutritional data across multiple food entries.

    This class aggregates nutritional information from multiple FoodEntry objects
    and performs complex calculations such as daily totals, goal tracking, and
    macro balance analysis. It provides insights into nutritional patterns and
    progress towards daily goals.

    Attributes:
        entries (list): List of FoodEntry objects to analyze
    """

    def __init__(self, entries):
        """
        Initializes the NutritionCalculator with a list of food entries.

        Args:
            entries (list): List of FoodEntry objects
        """
        self.entries = entries

    def get_daily_totals(self):
        """
        Calculates and returns the sum of all nutritional values across entries.

        Returns:
            dict: Dictionary with keys total_calories, total_protein, total_carbs,
                  total_fats, each containing the sum of values across all entries
        """
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0

        for entry in self.entries:
            total_calories += entry.calories
            total_protein += entry.protein
            total_carbs += entry.carbs
            total_fats += entry.fats

        return {
            'total_calories': round(total_calories, 1),
            'total_protein': round(total_protein, 1),
            'total_carbs': round(total_carbs, 1),
            'total_fats': round(total_fats, 1)
        }

    def get_goal_percentages(self, goals_dict):
        """
        Calculates the percentage of daily nutritional goals achieved.

        Args:
            goals_dict (dict): Dictionary with keys daily_calories, daily_protein,
                             daily_carbs, daily_fats containing goal values

        Returns:
            dict: Dictionary with keys calories_percent, protein_percent, carbs_percent,
                  fats_percent, each capped at 100 and rounded to 1 decimal place
        """
        totals = self.get_daily_totals()

        calories_percent = min((totals['total_calories'] / goals_dict['daily_calories']) * 100, 100)
        protein_percent = min((totals['total_protein'] / goals_dict['daily_protein']) * 100, 100)
        carbs_percent = min((totals['total_carbs'] / goals_dict['daily_carbs']) * 100, 100)
        fats_percent = min((totals['total_fats'] / goals_dict['daily_fats']) * 100, 100)

        return {
            'calories_percent': round(calories_percent, 1),
            'protein_percent': round(protein_percent, 1),
            'carbs_percent': round(carbs_percent, 1),
            'fats_percent': round(fats_percent, 1)
        }

    def get_macro_balance(self):
        """
        Analyzes macro balance and returns a classification string.

        Classifies the diet as:
        - "Protein focused" if protein provides >30% of total calories
        - "Balanced" if all macros are within 10% of ideal ratios (50% carbs, 30% protein, 20% fats)
        - "Carb heavy" otherwise

        Returns:
            str: One of "Protein focused", "Balanced", or "Carb heavy"
        """
        totals = self.get_daily_totals()

        if totals['total_calories'] == 0:
            return "No data"

        # Calculate percentage of calories from each macro (9 kcal per gram for fat and protein, 4 kcal per gram for carbs)
        protein_calories = totals['total_protein'] * 4
        carb_calories = totals['total_carbs'] * 4
        fat_calories = totals['total_fats'] * 9
        total_cals = protein_calories + carb_calories + fat_calories

        if total_cals == 0:
            return "No data"

        protein_percent = (protein_calories / total_cals) * 100
        carb_percent = (carb_calories / total_cals) * 100
        fat_percent = (fat_calories / total_cals) * 100

        # Check if protein focused (>30% of calories from protein)
        if protein_percent > 30:
            return "Protein focused"

        # Ideal ratios: 50% carbs, 30% protein, 20% fats
        ideal_carbs = 50
        ideal_protein = 30
        ideal_fats = 20
        tolerance = 10

        # Check if balanced (all within 10% of ideal)
        carb_balanced = abs(carb_percent - ideal_carbs) <= tolerance
        protein_balanced = abs(protein_percent - ideal_protein) <= tolerance
        fat_balanced = abs(fat_percent - ideal_fats) <= tolerance

        if carb_balanced and protein_balanced and fat_balanced:
            return "Balanced"

        return "Carb heavy"

    def get_highest_calorie_meal(self):
        """
        Finds and returns the food entry with the highest calorie content.

        Returns:
            FoodEntry: The food entry with the most calories, or None if no entries exist
        """
        if not self.entries:
            return None

        highest_entry = self.entries[0]
        for entry in self.entries:
            if entry.calories > highest_entry.calories:
                highest_entry = entry

        return highest_entry
