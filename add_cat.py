from api.models import Category
import os
import django

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pharmapoint.settings")
django.setup()


# Read the categories from the file and create Category objects
with open("categories.txt", "r") as file:
    for line in file:
        category_name = line.strip()
        if category_name:
            # Create a new Category object and save it
            category, created = Category.objects.get_or_create(
                name=category_name)
            if created:
                print(f"Category created: {category_name}")
            else:
                print(f"Category already exists: {category_name}")
