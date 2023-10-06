from django.core.management.base import BaseCommand
from api.models import Category


class Command(BaseCommand):
    help = 'Import categories from category.txt'

    def handle(self, *args, **options):
        # Define the path to the .txt file
        file_path = 'categories.txt'

        try:
            # Open the file for reading
            with open(file_path, 'r') as file:
                # Read the lines from the file
                lines = file.readlines()

                # Iterate over each line in the file
                for line in lines:
                    # Remove leading and trailing whitespace
                    category_name = line.strip()

                    # Check if a category with the same name already exists
                    if not Category.objects.filter(name=category_name).exists():
                        # Create a new Category object
                        category = Category(name=category_name)

                        # Save the new category to the database
                        category.save()

                        # Print a success message
                        self.stdout.write(self.style.SUCCESS(
                            f'Successfully created category: {category_name}'))

                # Print a message when the import is complete
                self.stdout.write(self.style.SUCCESS(
                    'Categories imported successfully.'))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {file_path}'))
