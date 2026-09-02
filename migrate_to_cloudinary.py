import os
import django

# 1. Setup Django environment
# Change 'core' to your actual project folder name if it is different
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')  
django.setup()

from store.models import Product  

def migrate_images():
    print("Starting image migration to Cloudinary...")
    
    # 2. Exclude empty or null fields using your actual field name: product_image
    products = Product.objects.exclude(product_image='').exclude(product_image__isnull=True)
    
    for product in products:
        # 3. Check if the file exists locally using the correct field name
        if product.product_image and os.path.exists(product.product_image.path):
            print(f"Uploading image for: {product.title}")
            
            # 4. Open the correct path
            with open(product.product_image.path, 'rb') as file_data:
                # 5. Extract the file name (e.g., 'photo.jpg') from the field name
                old_file_name = os.path.basename(product.product_image.name)
                
                # 6. Re-save using the correct field name: product_image
                product.product_image.save(old_file_name, file_data, save=True)
                
            print(f"Successfully uploaded: {product.product_image.url}")
        else:
            print(f"Skipping {product.title}: Local file not found at {product.product_image}")

    print("Migration finished!")

if __name__ == '__main__':
    migrate_images()
