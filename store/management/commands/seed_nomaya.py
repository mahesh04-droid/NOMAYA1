from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Product

PRODUCTS = [
    # Linen
    ('Printed Easy Drape', 'printed-easy-drape', 'A soft linen-forward drape designed for everyday movement.', 'linen', 'Indigo', 'pre-stitched', 2499, '/static/images/linen.jpg', '', 18, True),
    ('Terracotta Linen', 'terracotta-linen', 'Warm terracotta linen for relaxed festive dressing.', 'linen', 'Terracotta', 'classic', 2699, '/static/images/linen.jpg', '', 11, False),
    ('Ivory Linen Classic', 'ivory-linen-classic', 'Pure, unbleached linen with a calm, grounding feel.', 'linen', 'Ivory', 'classic', 2899, '/static/images/linen.jpg', '', 15, True),
    ('Mustard Easy Drape', 'mustard-easy-drape', 'Bright mustard tones on textured linen for effortless days.', 'linen', 'Mustard', 'easy', 2399, '/static/images/linen.jpg', '', 10, False),
    ('Sage Green Linen', 'sage-green-linen', 'A muted, earthy green linen that breathes with you.', 'linen', 'Sage', 'pre-stitched', 3199, '/static/images/linen.jpg', '', 22, True),
    ('Charcoal Linen Wrap', 'charcoal-linen-wrap', 'Deep, dramatic charcoal linen for evening comfort.', 'linen', 'Charcoal', 'easy', 2799, '/static/images/linen.jpg', '', 8, False),
    ('Rose Blush Linen', 'rose-blush-linen', 'Soft blush tones woven into durable, airy linen.', 'linen', 'Rose', 'classic', 2599, '/static/images/linen.jpg', '', 14, False),
    
    # Silk
    ('Midnight Silk', 'midnight-silk', 'Polished silk with a deep plum-blue finish.', 'silk', 'Midnight', 'classic', 5999, '/static/images/silk.jpg', '', 7, True),
    ('Bridal Rose Silk', 'bridal-rose-silk', 'A rich silk drape for celebrations and intimate ceremonies.', 'silk', 'Rose', 'pre-stitched', 7299, '/static/images/silk.jpg', '', 6, True),
    ('Emerald Green Silk', 'emerald-green-silk', 'Luxurious emerald silk that catches the light beautifully.', 'silk', 'Emerald', 'classic', 6499, '/static/images/silk.jpg', '', 4, True),
    ('Crimson Heritage Silk', 'crimson-heritage-silk', 'A timeless crimson silk drape, celebrating traditional craftsmanship.', 'silk', 'Crimson', 'pre-stitched', 7999, '/static/images/silk.jpg', '', 3, True),
    ('Ivory Pearl Silk', 'ivory-pearl-silk', 'Pristine ivory silk with a natural luminous sheen.', 'silk', 'Ivory', 'classic', 5899, '/static/images/silk.jpg', '', 9, False),
    ('Sapphire Silk Easy', 'sapphire-silk-easy', 'Deep sapphire tones in a modern, easy-to-wear silhouette.', 'silk', 'Sapphire', 'easy', 6299, '/static/images/silk.jpg', '', 12, False),
    ('Gold Zari Silk', 'gold-zari-silk', 'A stunning woven silk drape featuring intricate gold details.', 'silk', 'Gold', 'classic', 8999, '/static/images/silk.jpg', '', 2, True),
    ('Lavender Dream Silk', 'lavender-dream-silk', 'Soft lavender silk that moves like water.', 'silk', 'Lavender', 'easy', 5499, '/static/images/silk.jpg', '', 5, False),
    
    # Cotton
    ('Cobalt Easy Drape', 'cobalt-easy-drape', 'A vivid cobalt statement with an easy pre-stitched construction.', 'cotton', 'Cobalt', 'pre-stitched', 2999, '/static/images/cotton.jpg', '', 12, True),
    ('Garden Mist Cotton', 'garden-mist-cotton', 'Soft cotton chiffon with a botanical palette.', 'cotton', 'Sage', 'easy', 2399, '/static/images/cotton.jpg', '', 16, False),
    ('Turmeric Yellow Cotton', 'turmeric-yellow-cotton', 'Vibrant turmeric cotton for bright, sunny afternoons.', 'cotton', 'Yellow', 'classic', 1999, '/static/images/cotton.jpg', '', 25, False),
    ('Crimson Cotton Classic', 'crimson-cotton-classic', 'A lightweight classic cotton drape in bold crimson.', 'cotton', 'Crimson', 'classic', 2199, '/static/images/cotton.jpg', '', 18, False),
    ('Indigo Block Print', 'indigo-block-print', 'Traditional indigo block prints on breathable pure cotton.', 'cotton', 'Indigo', 'pre-stitched', 2799, '/static/images/cotton.jpg', '', 30, True),
    ('Mint Breeze Cotton', 'mint-breeze-cotton', 'Cooling mint green cotton, perfect for tropical climates.', 'cotton', 'Mint', 'easy', 1899, '/static/images/cotton.jpg', '', 40, False),
    ('Monochrome Ikat Cotton', 'monochrome-ikat-cotton', 'Striking black and white ikat patterns on everyday cotton.', 'cotton', 'Monochrome', 'classic', 2499, '/static/images/cotton.jpg', '', 15, True),
    
    # Chiffon
    ('Floral Garden Chiffon', 'floral-garden-chiffon', 'Airy floral chiffon for effortless occasions.', 'chiffon', 'Floral', 'easy', 2899, '/static/images/chiffon.jpg', '', 20, True),
    ('Blush Pink Chiffon', 'blush-pink-chiffon', 'A delicate, translucent blush pink drape.', 'chiffon', 'Pink', 'pre-stitched', 3299, '/static/images/chiffon.jpg', '', 12, False),
    ('Slate Grey Chiffon', 'slate-grey-chiffon', 'Modern slate grey in a flowing, weightless fabric.', 'chiffon', 'Grey', 'classic', 2799, '/static/images/chiffon.jpg', '', 18, False),
    ('Ruby Red Chiffon', 'ruby-red-chiffon', 'A romantic ruby red drape that flutters in the wind.', 'chiffon', 'Ruby', 'easy', 3499, '/static/images/chiffon.jpg', '', 10, True),
    ('Ocean Blue Chiffon', 'ocean-blue-chiffon', 'Cool oceanic blues on soft, draping chiffon.', 'chiffon', 'Blue', 'classic', 2999, '/static/images/chiffon.jpg', '', 22, False),
    ('Lilac Whisper Chiffon', 'lilac-whisper-chiffon', 'A whisper-light lilac drape for evening elegance.', 'chiffon', 'Lilac', 'pre-stitched', 3199, '/static/images/chiffon.jpg', '', 14, True),
    ('Sunset Orange Chiffon', 'sunset-orange-chiffon', 'Warm, glowing orange hues on sheer chiffon.', 'chiffon', 'Orange', 'easy', 2699, '/static/images/chiffon.jpg', '', 16, False),
    ('Emerald Chiffon Classic', 'emerald-chiffon-classic', 'Deep emerald green with a soft, matte chiffon finish.', 'chiffon', 'Emerald', 'classic', 2899, '/static/images/chiffon.jpg', '', 19, False),
]

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Product.objects.all().delete()
        for row in PRODUCTS:
            name, slug, desc, fabric, color, style, price, image, secondary, stock, featured = row
            Product.objects.create(
                name=name, slug=slug, description=desc, fabric=fabric, color=color, 
                style=style, price=price, image=image, secondary_image=secondary, 
                stock=stock, featured=featured
            )
            
        if not User.objects.filter(username='demo@nomaya.local').exists():
            User.objects.create_user(username='demo@nomaya.local', email='demo@nomaya.local', password='Nomaya@12345', first_name='Nomaya Demo')
            
        self.stdout.write(self.style.SUCCESS('NOMAYA seed complete with 30 local products.'))
