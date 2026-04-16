from django.core.management.base import BaseCommand
from accounts.models import University


class Command(BaseCommand):
    help = 'Seed initial universities'

    def handle(self, *args, **options):
        universities = [
            {'name': 'Cavendish University Uganda', 'short_name': 'CUU', 'email_domain': 'cavendish.ac.ug'},
            {'name': 'Makerere University', 'short_name': 'MAK', 'email_domain': 'mak.ac.ug'},
            {'name': 'Kampala International University', 'short_name': 'KIU', 'email_domain': 'kiu.ac.ug'},
            {'name': 'Uganda Christian University', 'short_name': 'UCU', 'email_domain': 'ucu.ac.ug'},
            {'name': 'Kyambogo University', 'short_name': 'KYU', 'email_domain': 'kyu.ac.ug'},
            {'name': 'Makerere University Business School', 'short_name': 'MUBS', 'email_domain': 'mubs.ac.ug'},
            {'name': 'Uganda Martyrs University', 'short_name': 'UMU', 'email_domain': 'umu.ac.ug'},
            {'name': 'Nkumba University', 'short_name': 'NKU', 'email_domain': 'nkumba.ac.ug'},
        ]

        created = 0
        for uni_data in universities:
            obj, was_created = University.objects.get_or_create(
                email_domain=uni_data['email_domain'],
                defaults=uni_data
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {obj.name}'))
            else:
                self.stdout.write(f'  Already exists: {obj.name}')

        self.stdout.write(self.style.SUCCESS(f'\nDone! Created {created} new universities.'))
