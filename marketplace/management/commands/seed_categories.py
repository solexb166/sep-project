from django.core.management.base import BaseCommand
from django.utils.text import slugify
from marketplace.models import Category
from skills.models import SkillCategory


class Command(BaseCommand):
    help = 'Seed marketplace and skill categories'

    def handle(self, *args, **options):
        marketplace_cats = [
            {'name': 'Textbooks & Study Materials', 'icon': 'bi-book-fill text-primary'},
            {'name': 'Electronics & Gadgets', 'icon': 'bi-laptop-fill text-info'},
            {'name': 'Furniture & Appliances', 'icon': 'bi-house-fill text-warning'},
            {'name': 'Clothing & Fashion', 'icon': 'bi-bag-fill text-danger'},
            {'name': 'Sports & Fitness', 'icon': 'bi-bicycle text-success'},
            {'name': 'Stationery & Art Supplies', 'icon': 'bi-pencil-fill text-secondary'},
            {'name': 'Food & Kitchen', 'icon': 'bi-cup-hot-fill text-warning'},
            {'name': 'Other', 'icon': 'bi-tag-fill text-muted'},
        ]

        skill_cats = [
            {'name': 'Academic Tutoring', 'icon': 'bi-mortarboard-fill text-primary'},
            {'name': 'IT & Tech Support', 'icon': 'bi-cpu-fill text-info'},
            {'name': 'Design & Creative', 'icon': 'bi-palette-fill text-danger'},
            {'name': 'Writing & Editing', 'icon': 'bi-pen-fill text-secondary'},
            {'name': 'Photography & Video', 'icon': 'bi-camera-fill text-dark'},
            {'name': 'Music & Arts', 'icon': 'bi-music-note-beamed text-success'},
            {'name': 'Languages & Translation', 'icon': 'bi-globe2 text-primary'},
            {'name': 'Business & Admin', 'icon': 'bi-briefcase-fill text-warning'},
            {'name': 'Fitness & Coaching', 'icon': 'bi-activity text-danger'},
            {'name': 'Other', 'icon': 'bi-stars text-warning'},
        ]

        self.stdout.write('Seeding marketplace categories...')
        for cat in marketplace_cats:
            obj, created = Category.objects.update_or_create(
                slug=slugify(cat['name']),
                defaults={'name': cat['name'], 'icon': cat['icon']}
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {obj.name}')

        self.stdout.write('\nSeeding skill categories...')
        for cat in skill_cats:
            obj, created = SkillCategory.objects.update_or_create(
                slug=slugify(cat['name']),
                defaults={'name': cat['name'], 'icon': cat['icon']}
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {obj.name}')

        self.stdout.write(self.style.SUCCESS('\nDone! All categories seeded.'))
